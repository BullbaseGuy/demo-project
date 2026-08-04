from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/devflow/validate_workflow_skills_lock.py"
SPEC = importlib.util.spec_from_file_location("workflow_skills_lock", MODULE_PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def fixture(root: Path) -> tuple[Path, bytes, bytes]:
    installer = b"#requires -Version 7.0\n"
    manifest = {
        "schema_version": "1.0.0",
        "release_version": "fixture",
        "source_repository": "BullbaseGuy/chatgpt-workflow-skills",
        "revision_policy": "exact-40-hex-commit",
        "entry_skill": "skills/workflow-router/SKILL.md",
        "files": [{"path": "skills/workflow-router/SKILL.md"}],
    }
    manifest_bytes = (json.dumps(manifest, separators=(",", ":")) + "\n").encode()
    lock = {
        "schema_version": 1,
        "source_repository": "BullbaseGuy/chatgpt-workflow-skills",
        "revision": "0123456789abcdef0123456789abcdef01234567",
        "release_version": "fixture",
        "manifest_path": "release/skills-manifest.json",
        "manifest_git_blob_sha": module.git_blob_sha(manifest_bytes),
        "installer_path": "scripts/install-workflow-skills.ps1",
        "installer_git_blob_sha": module.git_blob_sha(installer),
        "install_root": ".agents/workflow-skills",
        "entry_skill": "skills/workflow-router/SKILL.md",
        "payload_file_count": 1,
        "tracked_skill_bodies": False,
        "model_execution": "disabled",
        "codex_invocations": 0,
    }
    lock_path = root / ".devflow/workflow-skills.lock.json"
    lock_path.parent.mkdir(parents=True)
    lock_path.write_text(json.dumps(lock, indent=2) + "\n")
    return lock_path, manifest_bytes, installer


class WorkflowSkillsLockTests(unittest.TestCase):
    def test_valid_offline_lock(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            lock, manifest, installer = fixture(root)
            self.assertEqual(
                module.validate_lock(
                    root,
                    lock,
                    manifest_bytes=manifest,
                    installer_bytes=installer,
                ),
                [],
            )

    def test_branch_revision_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            lock, manifest, installer = fixture(root)
            value = json.loads(lock.read_text())
            value["revision"] = "main"
            lock.write_text(json.dumps(value))
            errors = module.validate_lock(
                root, lock, manifest_bytes=manifest, installer_bytes=installer
            )
            self.assertTrue(any("exact 40-character" in error for error in errors), errors)

    def test_manifest_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            lock, manifest, installer = fixture(root)
            errors = module.validate_lock(
                root,
                lock,
                manifest_bytes=manifest + b" ",
                installer_bytes=installer,
            )
            self.assertTrue(any("manifest blob mismatch" in error for error in errors), errors)

    def test_tracked_skill_body_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            lock, manifest, installer = fixture(root)
            copied = root / ".agents/workflow-skills/skills/copied/SKILL.md"
            copied.parent.mkdir(parents=True)
            copied.write_text("copied")
            errors = module.validate_lock(
                root, lock, manifest_bytes=manifest, installer_bytes=installer
            )
            self.assertTrue(any("tracked skill bodies" in error for error in errors), errors)

    def test_model_execution_must_stay_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            lock, manifest, installer = fixture(root)
            value = json.loads(lock.read_text())
            value["model_execution"] = "enabled"
            value["codex_invocations"] = 1
            lock.write_text(json.dumps(value))
            errors = module.validate_lock(
                root, lock, manifest_bytes=manifest, installer_bytes=installer
            )
            self.assertTrue(any("model execution" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
