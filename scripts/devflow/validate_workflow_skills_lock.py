from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen


class LockError(ValueError):
    pass


HEX40 = re.compile(r"^[0-9a-f]{40}$")
REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def git_blob_sha(data: bytes) -> str:
    prefix = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(prefix + data).hexdigest()  # noqa: S324 - Git object identity


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise LockError(f"expected JSON object: {path}")
    return value


def safe_path(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise LockError(f"{field} must be a non-empty string")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise LockError(f"{field} must be a normalized relative path")
    return path.as_posix()


def fetch_pinned(repository: str, revision: str, path: str) -> bytes:
    encoded = "/".join(quote(part, safe="") for part in path.split("/"))
    url = f"https://raw.githubusercontent.com/{repository}/{revision}/{encoded}"
    request = Request(url, headers={"User-Agent": "demo-project-workflow-skills-validator/1"})
    with urlopen(request, timeout=20) as response:
        return response.read()


def tracked_skill_bodies(repo_root: Path) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files"],
            check=True,
            capture_output=True,
            text=True,
        )
        paths = result.stdout.splitlines()
    except (OSError, subprocess.CalledProcessError):
        paths = [path.relative_to(repo_root).as_posix() for path in repo_root.rglob("SKILL.md")]
    forbidden = []
    for path in paths:
        normalized = PurePosixPath(path).as_posix()
        if normalized.endswith("/SKILL.md") and (
            normalized.startswith("skills/")
            or normalized.startswith(".agents/workflow-skills/")
        ):
            forbidden.append(normalized)
    return sorted(forbidden)


def validate_lock(
    repo_root: Path,
    lock_path: Path,
    *,
    manifest_bytes: bytes | None = None,
    installer_bytes: bytes | None = None,
) -> list[str]:
    errors: list[str] = []
    try:
        lock = load_object(lock_path)
    except (OSError, json.JSONDecodeError, LockError) as exc:
        return [str(exc)]

    required = {
        "schema_version",
        "source_repository",
        "revision",
        "release_version",
        "manifest_path",
        "manifest_git_blob_sha",
        "installer_path",
        "installer_git_blob_sha",
        "install_root",
        "entry_skill",
        "payload_file_count",
        "tracked_skill_bodies",
        "model_execution",
        "codex_invocations",
    }
    missing = sorted(required - lock.keys())
    if missing:
        errors.append("missing lock fields: " + ", ".join(missing))
        return errors

    repository = lock.get("source_repository")
    revision = lock.get("revision")
    if not isinstance(repository, str) or not REPOSITORY.fullmatch(repository):
        errors.append("source_repository must be owner/name")
    if not isinstance(revision, str) or not HEX40.fullmatch(revision):
        errors.append("revision must be an exact 40-character lowercase commit")

    for field in ("manifest_git_blob_sha", "installer_git_blob_sha"):
        value = lock.get(field)
        if not isinstance(value, str) or not HEX40.fullmatch(value):
            errors.append(f"{field} must be 40 lowercase hex characters")

    try:
        manifest_path = safe_path(lock.get("manifest_path"), "manifest_path")
        installer_path = safe_path(lock.get("installer_path"), "installer_path")
        safe_path(lock.get("install_root"), "install_root")
        entry_skill = safe_path(lock.get("entry_skill"), "entry_skill")
    except LockError as exc:
        errors.append(str(exc))
        return errors

    if lock.get("tracked_skill_bodies") is not False:
        errors.append("tracked_skill_bodies must be false")
    if lock.get("model_execution") != "disabled" or lock.get("codex_invocations") != 0:
        errors.append("model execution must remain disabled with codex_invocations=0")
    copied = tracked_skill_bodies(repo_root)
    if copied:
        errors.append("tracked skill bodies are forbidden: " + ", ".join(copied))

    if errors or not isinstance(repository, str) or not isinstance(revision, str):
        return errors

    try:
        manifest_bytes = manifest_bytes or fetch_pinned(repository, revision, manifest_path)
        installer_bytes = installer_bytes or fetch_pinned(repository, revision, installer_path)
    except Exception as exc:
        errors.append(f"pinned source fetch failed: {type(exc).__name__}: {exc}")
        return errors

    manifest_sha = git_blob_sha(manifest_bytes)
    installer_sha = git_blob_sha(installer_bytes)
    if manifest_sha != lock["manifest_git_blob_sha"]:
        errors.append(
            f"manifest blob mismatch: lock={lock['manifest_git_blob_sha']}, actual={manifest_sha}"
        )
    if installer_sha != lock["installer_git_blob_sha"]:
        errors.append(
            f"installer blob mismatch: lock={lock['installer_git_blob_sha']}, actual={installer_sha}"
        )

    try:
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f"manifest is not valid UTF-8 JSON: {exc}")
        return errors

    if not isinstance(manifest, dict):
        errors.append("manifest root must be an object")
        return errors
    if manifest.get("source_repository") != repository:
        errors.append("manifest source_repository differs from lock")
    if manifest.get("release_version") != lock.get("release_version"):
        errors.append("manifest release_version differs from lock")
    if manifest.get("revision_policy") != "exact-40-hex-commit":
        errors.append("manifest revision policy is not immutable")
    files = manifest.get("files")
    if not isinstance(files, list) or len(files) != lock.get("payload_file_count"):
        errors.append("manifest payload_file_count differs from lock")
    elif entry_skill not in {entry.get("path") for entry in files if isinstance(entry, dict)}:
        errors.append("entry_skill is not present in manifest")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the pinned workflow-skills consumer lock")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--lock", type=Path, default=Path(".devflow/workflow-skills.lock.json"))
    parser.add_argument("--manifest-file", type=Path)
    parser.add_argument("--installer-file", type=Path)
    args = parser.parse_args()

    manifest_bytes = args.manifest_file.read_bytes() if args.manifest_file else None
    installer_bytes = args.installer_file.read_bytes() if args.installer_file else None
    errors = validate_lock(
        args.repo_root,
        args.lock,
        manifest_bytes=manifest_bytes,
        installer_bytes=installer_bytes,
    )
    if errors:
        print(json.dumps({"status": "FAIL", "errors": errors}, indent=2))
        return 1
    print(json.dumps({"status": "PASS", "lock": str(args.lock)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
