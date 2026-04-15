"""Renumber indexed keys in an env dict (e.g. ITEM_1, ITEM_2 -> ITEM_1, ITEM_2 after gaps)."""

from __future__ import annotations

import re
from typing import Dict, List, Tuple


class RenumbererError(Exception):
    """Raised when renumbering fails."""


def _indexed_groups(env: Dict[str, str], prefix: str) -> List[Tuple[str, str, int]]:
    """Return (key, value, index) tuples for keys matching <prefix>_<int>."""
    pattern = re.compile(rf"^{re.escape(prefix)}_(\d+)$", re.IGNORECASE)
    results = []
    for key, value in env.items():
        m = pattern.match(key)
        if m:
            results.append((key, value, int(m.group(1))))
    results.sort(key=lambda t: t[2])
    return results


def find_gaps(env: Dict[str, str], prefix: str) -> List[int]:
    """Return a sorted list of missing indices in the sequence for a prefix."""
    groups = _indexed_groups(env, prefix)
    if not groups:
        return []
    indices = [t[2] for t in groups]
    full = set(range(min(indices), max(indices) + 1))
    return sorted(full - set(indices))


def renumber_prefix(
    env: Dict[str, str],
    prefix: str,
    start: int = 1,
) -> Dict[str, str]:
    """Renumber all <prefix>_N keys so they form a contiguous sequence from *start*."""
    if not prefix:
        raise RenumbererError("prefix must not be empty")
    groups = _indexed_groups(env, prefix)
    if not groups:
        return dict(env)

    result = {k: v for k, v in env.items() if not any(k == g[0] for g in groups)}
    for new_idx, (_, value, _orig) in enumerate(groups, start=start):
        new_key = f"{prefix}_{new_idx}"
        result[new_key] = value
    return result


def get_renumber_preview(
    env: Dict[str, str],
    prefix: str,
    start: int = 1,
) -> List[Tuple[str, str]]:
    """Return list of (old_key, new_key) pairs that would change during renumbering."""
    groups = _indexed_groups(env, prefix)
    preview = []
    for new_idx, (old_key, _value, _orig) in enumerate(groups, start=start):
        new_key = f"{prefix}_{new_idx}"
        if old_key != new_key:
            preview.append((old_key, new_key))
    return preview
