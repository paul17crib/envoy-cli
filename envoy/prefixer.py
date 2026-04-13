"""Prefix management utilities for env keys."""

from typing import Dict, List, Optional


class PrefixError(Exception):
    """Raised when a prefix operation fails."""


def add_prefix(env: Dict[str, str], prefix: str, keys: Optional[List[str]] = None) -> Dict[str, str]:
    """Return a new env dict with prefix added to specified keys (or all keys)."""
    if not prefix:
        raise PrefixError("Prefix must not be empty.")
    result = {}
    for key, value in env.items():
        if keys is None or key in keys:
            new_key = f"{prefix}{key}"
            if new_key in env and new_key not in (keys or []):
                raise PrefixError(f"Adding prefix would create duplicate key: {new_key!r}")
            result[new_key] = value
        else:
            result[key] = value
    return result


def remove_prefix(env: Dict[str, str], prefix: str, keys: Optional[List[str]] = None) -> Dict[str, str]:
    """Return a new env dict with prefix stripped from matching keys."""
    if not prefix:
        raise PrefixError("Prefix must not be empty.")
    result = {}
    for key, value in env.items():
        if key.startswith(prefix) and (keys is None or key in keys):
            stripped = key[len(prefix):]
            if not stripped:
                raise PrefixError(f"Removing prefix from {key!r} would produce an empty key.")
            result[stripped] = value
        else:
            result[key] = value
    return result


def list_prefixed_keys(env: Dict[str, str], prefix: str) -> List[str]:
    """Return all keys in env that start with the given prefix."""
    return [k for k in env if k.startswith(prefix)]


def rename_prefix(env: Dict[str, str], old_prefix: str, new_prefix: str) -> Dict[str, str]:
    """Replace old_prefix with new_prefix on all matching keys."""
    if not old_prefix:
        raise PrefixError("Old prefix must not be empty.")
    if new_prefix is None:
        raise PrefixError("New prefix must not be None.")
    stripped = remove_prefix(env, old_prefix)
    matching = list_prefixed_keys(env, old_prefix)
    stripped_keys = [k[len(old_prefix):] for k in matching]
    return add_prefix(stripped, new_prefix, keys=stripped_keys)
