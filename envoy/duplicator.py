"""Duplicator: copy keys within an env dict under new names."""

from __future__ import annotations

from typing import Dict, List, Optional


class DuplicatorError(Exception):
    """Raised when a duplication operation cannot be completed."""


def duplicate_key(
    env: Dict[str, str],
    source: str,
    dest: str,
    overwrite: bool = False,
) -> Dict[str, str]:
    """Return a new env with *source* copied to *dest*.

    Raises DuplicatorError if *source* is missing or *dest* already exists
    and *overwrite* is False.
    """
    if source not in env:
        raise DuplicatorError(f"Source key '{source}' not found in env.")
    if dest in env and not overwrite:
        raise DuplicatorError(
            f"Destination key '{dest}' already exists. Use overwrite=True to replace it."
        )
    result = dict(env)
    result[dest] = env[source]
    return result


def duplicate_keys(
    env: Dict[str, str],
    mapping: Dict[str, str],
    overwrite: bool = False,
) -> Dict[str, str]:
    """Duplicate multiple keys at once using a {source: dest} *mapping*.

    Returns a new env dict with all copies applied.
    """
    result = dict(env)
    for source, dest in mapping.items():
        result = duplicate_key(result, source, dest, overwrite=overwrite)
    return result


def get_duplicated_keys(
    original: Dict[str, str],
    updated: Dict[str, str],
) -> List[str]:
    """Return list of keys that are present in *updated* but not in *original*."""
    return [k for k in updated if k not in original]


def preview_duplications(
    env: Dict[str, str],
    mapping: Dict[str, str],
) -> List[Dict[str, Optional[str]]]:
    """Return a preview list describing each planned duplication.

    Each entry has keys: source, dest, value, conflict.
    """
    preview = []
    for source, dest in mapping.items():
        preview.append({
            "source": source,
            "dest": dest,
            "value": env.get(source),
            "conflict": dest in env,
        })
    return preview
