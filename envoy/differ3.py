"""Three-way merge diff for .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class ThreeWayEntry:
    key: str
    base: Optional[str]
    ours: Optional[str]
    theirs: Optional[str]

    @property
    def has_conflict(self) -> bool:
        """True when ours and theirs diverge from base in incompatible ways."""
        if self.ours == self.theirs:
            return False
        if self.ours is None or self.theirs is None:
            return True
        return self.ours != self.theirs and self.base != self.ours and self.base != self.theirs

    @property
    def symbol(self) -> str:
        if self.has_conflict:
            return "!"
        if self.ours is None and self.theirs is not None:
            return "-"
        if self.ours is not None and self.theirs is None:
            return "+"
        if self.base != self.ours:
            return "~"
        return "="


@dataclass
class ThreeWayReport:
    entries: List[ThreeWayEntry] = field(default_factory=list)

    @property
    def conflicts(self) -> List[ThreeWayEntry]:
        return [e for e in self.entries if e.has_conflict]

    @property
    def conflict_keys(self) -> List[str]:
        return [e.key for e in self.conflicts]

    @property
    def has_conflicts(self) -> bool:
        return bool(self.conflicts)

    def auto_resolved(self) -> Dict[str, str]:
        """Return keys that can be auto-resolved (one side unchanged from base)."""
        result: Dict[str, str] = {}
        for e in self.entries:
            if e.has_conflict:
                continue
            if e.ours is not None:
                result[e.key] = e.ours
            elif e.theirs is not None:
                result[e.key] = e.theirs
        return result


def three_way_diff(
    base: Dict[str, str],
    ours: Dict[str, str],
    theirs: Dict[str, str],
) -> ThreeWayReport:
    """Compute a three-way diff between base, ours, and theirs."""
    all_keys: Set[str] = set(base) | set(ours) | set(theirs)
    entries: List[ThreeWayEntry] = []
    for key in sorted(all_keys):
        entries.append(
            ThreeWayEntry(
                key=key,
                base=base.get(key),
                ours=ours.get(key),
                theirs=theirs.get(key),
            )
        )
    return ThreeWayReport(entries=entries)
