from __future__ import annotations

from pathlib import Path

from config import load_gate_profiles


def get_gate_profile(
    name: str,
    root: Path = Path("."),
) -> list[list[str]]:
    profiles = load_gate_profiles(root)
    try:
        commands = profiles[name]
    except KeyError as exc:
        raise ValueError(
            f"unknown gate profile: {name}"
        ) from exc
    return [list(command) for command in commands]
