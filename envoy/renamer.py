"""Bulk key renaming utilities for .env files."""

from typing import Dict, List, Optional, Tuple


class RenameError(Exception):
    """Raised when a rename operation cannot be completed."""


class RenameResult:
    """Holds the outcome of a bulk rename operation."""

    def __init__(self) -> None:
        self.renamed: List[Tuple[str, str]] = []   # (old_key, new_key)
        self.skipped: List[Tuple[str, str]] = []   # (old_key, reason)

    @property
    def total_renamed(self) -> int:
        return len(self.renamed)

    @property
    def total_skipped(self) -> int:
        return len(self.skipped)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"RenameResult(renamed={self.total_renamed}, "
            f"skipped={self.total_skipped})"
        )


def rename_key(
    env: Dict[str, str],
    old_key: str,
    new_key: str,
    overwrite: bool = False,
) -> Dict[str, str]:
    """Return a new env dict with *old_key* renamed to *new_key*.

    Raises RenameError if *old_key* is absent or *new_key* already exists
    and *overwrite* is False.
    """
    if old_key not in env:
        raise RenameError(f"Key '{old_key}' not found in env.")
    if new_key in env and not overwrite:
        raise RenameError(
            f"Key '{new_key}' already exists. Use overwrite=True to replace it."
        )
    result = {}
    for k, v in env.items():
        if k == old_key:
            result[new_key] = v
        elif k != new_key or not overwrite:
            result[k] = v
    return result


def bulk_rename(
    env: Dict[str, str],
    mapping: Dict[str, str],
    overwrite: bool = False,
    skip_missing: bool = False,
) -> Tuple[Dict[str, str], RenameResult]:
    """Apply multiple renames described by *mapping* {old_key: new_key}.

    Returns the updated env dict and a RenameResult summary.
    If *skip_missing* is True, absent source keys are recorded as skipped
    rather than raising an error.
    """
    result = RenameResult()
    current = dict(env)

    for old_key, new_key in mapping.items():
        if old_key not in current:
            if skip_missing:
                result.skipped.append((old_key, "key not found"))
                continue
            raise RenameError(f"Key '{old_key}' not found in env.")

        if new_key in current and not overwrite:
            result.skipped.append((old_key, f"target '{new_key}' already exists"))
            continue

        current = rename_key(current, old_key, new_key, overwrite=overwrite)
        result.renamed.append((old_key, new_key))

    return current, result


def format_rename_report(result: RenameResult) -> str:
    """Return a human-readable summary of a RenameResult."""
    lines: List[str] = []
    for old_key, new_key in result.renamed:
        lines.append(f"  renamed: {old_key} -> {new_key}")
    for key, reason in result.skipped:
        lines.append(f"  skipped: {key} ({reason})")
    if not lines:
        lines.append("  no changes made")
    return "\n".join(lines)
