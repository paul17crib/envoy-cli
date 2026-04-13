"""Bulk rename keys in an env dict using a prefix swap or mapping."""

from __future__ import annotations

from typing import Dict, Optional


class BulkRenameError(Exception):
    pass


def rename_by_mapping(
    env: Dict[str, str],
    mapping: Dict[str, str],
    overwrite: bool = False,
) -> Dict[str, str]:
    """Rename keys according to an explicit old->new mapping.

    Raises BulkRenameError if a target key already exists and overwrite is False.
    Missing source keys are silently skipped.
    """
    result = dict(env)
    for old_key, new_key in mapping.items():
        if old_key not in result:
            continue
        if new_key in result and not overwrite:
            raise BulkRenameError(
                f"Cannot rename '{old_key}' to '{new_key}': target key already exists."
            )
        result[new_key] = result.pop(old_key)
    return result


def rename_prefix(
    env: Dict[str, str],
    old_prefix: str,
    new_prefix: str,
    overwrite: bool = False,
) -> Dict[str, str]:
    """Replace old_prefix with new_prefix on all matching keys."""
    if not old_prefix:
        raise BulkRenameError("old_prefix must not be empty.")
    mapping = {
        key: new_prefix + key[len(old_prefix):]
        for key in env
        if key.startswith(old_prefix)
    }
    return rename_by_mapping(env, mapping, overwrite=overwrite)


def get_rename_preview(
    env: Dict[str, str],
    mapping: Dict[str, str],
) -> Dict[str, Optional[str]]:
    """Return a dict of old_key -> new_key for keys that would be renamed.

    Keys not present in env are excluded from the preview.
    """
    return {
        old: new
        for old, new in mapping.items()
        if old in env
    }
