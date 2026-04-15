"""Counter module: count occurrences of patterns in env values."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class CounterError(Exception):
    pass


@dataclass
class CountResult:
    key: str
    value: str
    count: int
    matches: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"CountResult(key={self.key!r}, count={self.count})"


def count_in_value(
    value: str,
    pattern: str,
    *,
    regex: bool = False,
    case_sensitive: bool = False,
) -> List[str]:
    """Return all matches of pattern within value."""
    if not pattern:
        raise CounterError("Pattern must not be empty.")
    flags = 0 if case_sensitive else re.IGNORECASE
    if not regex:
        pattern = re.escape(pattern)
    try:
        return re.findall(pattern, value, flags=flags)
    except re.error as exc:
        raise CounterError(f"Invalid regex pattern: {exc}") from exc


def count_env(
    env: Dict[str, str],
    pattern: str,
    *,
    keys: Optional[List[str]] = None,
    regex: bool = False,
    case_sensitive: bool = False,
    include_keys: bool = False,
) -> List[CountResult]:
    """Count pattern occurrences across env values (and optionally keys)."""
    results: List[CountResult] = []
    targets = {k: v for k, v in env.items() if keys is None or k in keys}
    for k, v in targets.items():
        search_text = f"{k}={v}" if include_keys else v
        matches = count_in_value(search_text, pattern, regex=regex, case_sensitive=case_sensitive)
        results.append(CountResult(key=k, value=v, count=len(matches), matches=matches))
    return results


def total_matches(results: List[CountResult]) -> int:
    """Sum all match counts across results."""
    return sum(r.count for r in results)


def get_matching_keys(results: List[CountResult]) -> List[str]:
    """Return keys that had at least one match."""
    return [r.key for r in results if r.count > 0]
