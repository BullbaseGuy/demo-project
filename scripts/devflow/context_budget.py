from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class ContextBudgetError(ValueError):
    pass


@dataclass(frozen=True)
class ContextBudget:
    max_allowed_files: int = 5
    max_task_bytes: int = 32768
    max_total_allowed_file_bytes: int = 262144
    max_single_file_bytes: int = 131072
    max_log_excerpt_lines: int = 300
    include_chat_history: bool = False
    include_full_sop: bool = False

    @classmethod
    def from_mapping(cls, value: object) -> ContextBudget:
        if not isinstance(value, dict):
            raise ContextBudgetError(
                "context_budget must be an object"
            )
        defaults = cls()
        allowed = set(defaults.__dict__)
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise ContextBudgetError(
                "unknown context budget field(s): "
                + ", ".join(unknown)
            )
        raw = {**defaults.__dict__, **value}
        for key in (
            "max_allowed_files",
            "max_task_bytes",
            "max_total_allowed_file_bytes",
            "max_single_file_bytes",
            "max_log_excerpt_lines",
        ):
            item = raw[key]
            if (
                not isinstance(item, int)
                or isinstance(item, bool)
                or item <= 0
            ):
                raise ContextBudgetError(
                    f"{key} must be a positive integer"
                )
        for key in (
            "include_chat_history",
            "include_full_sop",
        ):
            if not isinstance(raw[key], bool):
                raise ContextBudgetError(
                    f"{key} must be boolean"
                )
            if raw[key]:
                raise ContextBudgetError(
                    f"{key} must remain false"
                )
        if (
            raw["max_single_file_bytes"]
            > raw["max_total_allowed_file_bytes"]
        ):
            raise ContextBudgetError(
                "max_single_file_bytes cannot exceed total"
            )
        return cls(**raw)


def inspect_allowed_files(
    root: Path,
    paths: tuple[str, ...],
    budget: ContextBudget,
) -> dict[str, object]:
    if len(paths) > budget.max_allowed_files:
        return {
            "status": "FAIL",
            "reason": "TOO_MANY_FILES",
        }
    sizes = {}
    total = 0
    for item in paths:
        path = root / item
        size = (
            path.stat().st_size
            if path.exists() and path.is_file()
            else 0
        )
        sizes[item] = size
        total += size
        if size > budget.max_single_file_bytes:
            return {
                "status": "FAIL",
                "reason": "SINGLE_FILE_TOO_LARGE",
                "sizes": sizes,
            }
    if total > budget.max_total_allowed_file_bytes:
        return {
            "status": "FAIL",
            "reason": "TOTAL_FILES_TOO_LARGE",
            "sizes": sizes,
        }
    return {
        "status": "PASS",
        "total_bytes": total,
        "sizes": sizes,
    }
