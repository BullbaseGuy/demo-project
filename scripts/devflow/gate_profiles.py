from __future__ import annotations

from config import load_gate_profiles


def get_gate_profile(name: str) -> list[list[str]]:
    profiles = load_gate_profiles()
    try:
        commands = profiles[name]
    except KeyError as exc:
        raise ValueError(
            f"unknown gate profile: {name}"
        ) from exc
    return [list(command) for command in commands]
