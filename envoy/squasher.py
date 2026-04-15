"""squasher.py — Squash duplicate or redundant keys from an env dict,
keeping only the last occurrence (or first, depending on strategy).
"""

from __future__ import annotations

from typing import Dict, List, Literal, Tuple

SquashStrategy = Literal["last", "first"]


class SquashError(Exception):
    """Raised when squashing fails due to invalid input."""


def find_duplicate_keys(lines: List[str]) -> Dict[str, List[int]]:
    """Return a mapping of key -> list of line indices where it appears.

    Only keys that appear more than once are included.
    """
    seen: Dict[str, List[int]] = {}
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key = stripped.split("=", 1)[0].strip()
        seen.setdefault(key, []).append(idx)
    return {k: v for k, v in seen.items() if len(v) > 1}


def squash_lines(
    lines: List[str],
    strategy: SquashStrategy = "last",
) -> Tuple[List[str], Dict[str, int]]:
    """Remove duplicate key lines, keeping either the first or last occurrence.

    Returns:
        (squashed_lines, removed_counts) where removed_counts maps each
        squashed key to the number of lines that were dropped.
    """
    duplicates = find_duplicate_keys(lines)
    if not duplicates:
        return list(lines), {}

    lines_to_drop: set[int] = set()
    removed_counts: Dict[str, int] = {}

    for key, indices in duplicates.items():
        if strategy == "last":
            drop = indices[:-1]
        else:
            drop = indices[1:]
        lines_to_drop.update(drop)
        removed_counts[key] = len(drop)

    squashed = [line for idx, line in enumerate(lines) if idx not in lines_to_drop]
    return squashed, removed_counts


def squash_env(
    env: Dict[str, str],
) -> Dict[str, str]:
    """Return a copy of *env* (no-op since dicts have unique keys).

    Provided for API symmetry; real squashing operates on raw line lists.
    """
    return dict(env)


def format_squash_report(
    removed_counts: Dict[str, int],
    source: str = "",
) -> str:
    """Return a human-readable summary of squash results."""
    if not removed_counts:
        label = f" in {source}" if source else ""
        return f"No duplicate keys found{label}."
    lines = [f"Squashed {len(removed_counts)} key(s):"]
    for key, count in sorted(removed_counts.items()):
        lines.append(f"  {key}: removed {count} duplicate line(s)")
    return "\n".join(lines)
