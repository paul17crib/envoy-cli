"""Reorder keys in an env mapping according to a given key order list."""

from __future__ import annotations

from typing import Dict, List, Optional


class ReorderError(Exception):
    """Raised when reordering cannot be completed."""


def reorder_env(
    env: Dict[str, str],
    order: List[str],
    *,
    missing_ok: bool = True,
    append_remaining: bool = True,
) -> Dict[str, str]:
    """Return a new dict with keys arranged according to *order*.

    Args:
        env: Source environment mapping.
        order: Desired key order. Keys not present in *env* are skipped unless
            *missing_ok* is False, in which case a :class:`ReorderError` is raised.
        missing_ok: If False, raise when a key in *order* is absent from *env*.
        append_remaining: If True, keys in *env* that are not listed in *order*
            are appended at the end in their original insertion order.

    Returns:
        A new ordered dict.
    """
    if not missing_ok:
        absent = [k for k in order if k not in env]
        if absent:
            raise ReorderError(
                f"Keys not found in env: {', '.join(absent)}"
            )

    result: Dict[str, str] = {}
    for key in order:
        if key in env:
            result[key] = env[key]

    if append_remaining:
        for key, value in env.items():
            if key not in result:
                result[key] = value

    return result


def get_reorder_preview(
    env: Dict[str, str],
    order: List[str],
    *,
    append_remaining: bool = True,
) -> List[str]:
    """Return the list of keys in the order they would appear after reordering.

    Useful for dry-run output without materialising the full mapping.
    """
    seen: set = set()
    preview: List[str] = []

    for key in order:
        if key in env:
            preview.append(key)
            seen.add(key)

    if append_remaining:
        for key in env:
            if key not in seen:
                preview.append(key)

    return preview


def move_key(
    env: Dict[str, str],
    key: str,
    position: int,
) -> Dict[str, str]:
    """Move *key* to a specific *position* (0-based) in the mapping.

    Raises :class:`ReorderError` if *key* is not present in *env*.
    """
    if key not in env:
        raise ReorderError(f"Key '{key}' not found in env.")

    keys = [k for k in env if k != key]
    position = max(0, min(position, len(keys)))
    keys.insert(position, key)
    return {k: env[k] for k in keys}
