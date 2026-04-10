"""Core diff logic for comparing two env dictionaries."""

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class DiffEntry:
    key: str
    symbol: str  # '+', '-', '~', '='
    old_value: str | None
    new_value: str | None

    @property
    def is_added(self) -> bool:
        return self.symbol == "+"

    @property
    def is_removed(self) -> bool:
        return self.symbol == "-"

    @property
    def is_changed(self) -> bool:
        return self.symbol == "~"

    @property
    def is_unchanged(self) -> bool:
        return self.symbol == "="


def compute_diff(
    base: Dict[str, str],
    target: Dict[str, str],
    include_unchanged: bool = False,
) -> List[DiffEntry]:
    """Compute a diff between two env dicts.

    Returns a list of DiffEntry objects sorted by key.
    """
    all_keys = sorted(set(base) | set(target))
    entries: List[DiffEntry] = []

    for key in all_keys:
        in_base = key in base
        in_target = key in target

        if in_base and not in_target:
            entries.append(DiffEntry(key, "-", base[key], None))
        elif not in_base and in_target:
            entries.append(DiffEntry(key, "+", None, target[key]))
        elif base[key] != target[key]:
            entries.append(DiffEntry(key, "~", base[key], target[key]))
        elif include_unchanged:
            entries.append(DiffEntry(key, "=", base[key], target[key]))

    return entries


def diff_summary(entries: List[DiffEntry]) -> Tuple[int, int, int]:
    """Return (added, removed, changed) counts from a diff."""
    added = sum(1 for e in entries if e.is_added)
    removed = sum(1 for e in entries if e.is_removed)
    changed = sum(1 for e in entries if e.is_changed)
    return added, removed, changed
