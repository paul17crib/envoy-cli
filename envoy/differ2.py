"""Multi-file diff engine for comparing two or more .env files side by side."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class MultiDiffEntry:
    key: str
    values: Dict[str, Optional[str]]  # filename -> value (None = missing)

    @property
    def is_consistent(self) -> bool:
        """True when every file has the same non-None value."""
        present = [v for v in self.values.values() if v is not None]
        return len(present) == len(self.values) and len(set(present)) == 1

    @property
    def is_missing_in_some(self) -> bool:
        return any(v is None for v in self.values.values())

    @property
    def has_value_conflict(self) -> bool:
        present = [v for v in self.values.values() if v is not None]
        return len(set(present)) > 1


@dataclass
class MultiDiffReport:
    files: List[str]
    entries: List[MultiDiffEntry] = field(default_factory=list)

    @property
    def consistent_keys(self) -> List[str]:
        return [e.key for e in self.entries if e.is_consistent]

    @property
    def conflicting_keys(self) -> List[str]:
        return [e.key for e in self.entries if e.has_value_conflict]

    @property
    def missing_keys(self) -> List[str]:
        return [e.key for e in self.entries if e.is_missing_in_some]


def multi_diff(envs: Dict[str, Dict[str, str]]) -> MultiDiffReport:
    """Produce a MultiDiffReport comparing all provided envs.

    Args:
        envs: mapping of filename -> parsed env dict.

    Returns:
        MultiDiffReport with one entry per unique key across all files.
    """
    files = list(envs.keys())
    all_keys: Set[str] = set()
    for env in envs.values():
        all_keys.update(env.keys())

    entries: List[MultiDiffEntry] = []
    for key in sorted(all_keys):
        values = {fname: envs[fname].get(key) for fname in files}
        entries.append(MultiDiffEntry(key=key, values=values))

    return MultiDiffReport(files=files, entries=entries)
