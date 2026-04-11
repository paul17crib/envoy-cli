"""Deduplication utilities for .env files."""

from typing import Dict, List, Tuple


class DuplicateEntry:
    """Represents a duplicate key found in an env mapping."""

    def __init__(self, key: str, occurrences: int, kept_value: str):
        self.key = key
        self.occurrences = occurrences
        self.kept_value = kept_value

    def __repr__(self) -> str:  # pragma: no cover
        return f"DuplicateEntry(key={self.key!r}, occurrences={self.occurrences}, kept={self.kept_value!r})"


def find_duplicates(lines: List[str]) -> Dict[str, List[str]]:
    """Scan raw env lines and return a mapping of key -> list of all values seen."""
    seen: Dict[str, List[str]] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip()
        seen.setdefault(key, []).append(value)
    return {k: v for k, v in seen.items() if len(v) > 1}


def deduplicate_env(
    env: Dict[str, str],
    lines: List[str],
    strategy: str = "last",
) -> Tuple[Dict[str, str], List[DuplicateEntry]]:
    """Return a deduplicated env dict and a list of duplicate entries found.

    Args:
        env: Already-parsed env dict (last-value-wins from parser).
        lines: Raw lines from the source file for duplicate detection.
        strategy: 'last' keeps the last occurrence (default); 'first' keeps the first.

    Returns:
        A tuple of (deduped_env, duplicate_entries).
    """
    duplicates_map = find_duplicates(lines)

    if not duplicates_map:
        return dict(env), []

    result: Dict[str, str] = {}
    entries: List[DuplicateEntry] = []

    # Build ordered key list from lines preserving first-seen order
    ordered_keys: List[str] = []
    first_values: Dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip()
        if key not in first_values:
            first_values[key] = value
            ordered_keys.append(key)

    for key in ordered_keys:
        if key in duplicates_map:
            kept = first_values[key] if strategy == "first" else env.get(key, first_values[key])
            result[key] = kept
            entries.append(DuplicateEntry(key, len(duplicates_map[key]), kept))
        else:
            result[key] = env.get(key, first_values.get(key, ""))

    return result, entries


def format_duplicate_report(entries: List[DuplicateEntry]) -> str:
    """Return a human-readable report of duplicate keys."""
    if not entries:
        return "No duplicate keys found."
    lines = [f"Found {len(entries)} duplicate key(s):"]
    for e in entries:
        lines.append(f"  {e.key}: {e.occurrences} occurrences, kept value={e.kept_value!r}")
    return "\n".join(lines)
