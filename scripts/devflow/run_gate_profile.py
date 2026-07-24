from __future__ import annotations

import argparse
import json
import queue
import subprocess
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

from gate_profiles import get_gate_profile


def utc_now() -> str:
    return (
        datetime.now(UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def run_command(
    command: list[str],
    heartbeat_seconds: int,
    workdir: Path,
) -> tuple[int, float]:
    started = time.monotonic()
    process = subprocess.Popen(
        command,
        cwd=workdir,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )
    output: queue.Queue[str | None] = queue.Queue()

    def reader() -> None:
        assert process.stdout is not None
        for line in process.stdout:
            output.put(line)
        output.put(None)

    thread = threading.Thread(
        target=reader,
        daemon=True,
    )
    thread.start()
    last_output = time.monotonic()
    complete = False
    while not complete:
        try:
            item = output.get(timeout=1)
        except queue.Empty:
            item = ""
        if item is None:
            complete = True
        elif item:
            print(item, end="", flush=True)
            last_output = time.monotonic()
        if (
            process.poll() is None
            and time.monotonic() - last_output >= heartbeat_seconds
        ):
            elapsed = int(time.monotonic() - started)
            print(
                f"[heartbeat] utc={utc_now()} "
                f"elapsed_seconds={elapsed}",
                flush=True,
            )
            last_output = time.monotonic()
    return (
        process.wait(),
        round(time.monotonic() - started, 3),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("profile")
    parser.add_argument(
        "--config-root",
        type=Path,
        default=Path("."),
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        default=Path("."),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("devflow-gate-result.json"),
    )
    parser.add_argument(
        "--heartbeat-seconds",
        type=int,
        default=30,
    )
    args = parser.parse_args()
    if args.heartbeat_seconds < 5:
        raise SystemExit(
            "heartbeat must be at least five seconds"
        )

    config_root = args.config_root.resolve()
    workdir = args.workdir.resolve()
    if not config_root.is_dir():
        raise SystemExit(
            f"config root does not exist: {config_root}"
        )
    if not workdir.is_dir():
        raise SystemExit(
            f"workdir does not exist: {workdir}"
        )

    commands = get_gate_profile(
        args.profile,
        config_root,
    )
    results = []
    overall = 0
    for command in commands:
        print(
            f"[gate:{args.profile}] running: {command}",
            flush=True,
        )
        code, elapsed = run_command(
            command,
            args.heartbeat_seconds,
            workdir,
        )
        results.append(
            {
                "command": command,
                "return_code": code,
                "elapsed_seconds": elapsed,
            }
        )
        if code != 0:
            overall = code or 1
            break

    summary = {
        "profile": args.profile,
        "status": "PASS" if overall == 0 else "FAIL",
        "config_root": config_root.as_posix(),
        "workdir": workdir.as_posix(),
        "commands": results,
        "completed_at_utc": utc_now(),
    }
    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    args.output.write_text(
        json.dumps(
            summary,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        f"GATE_PROFILE_STATUS={summary['status']}"
    )
    return overall


if __name__ == "__main__":
    raise SystemExit(main())
