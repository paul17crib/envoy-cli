"""Scope filtering: restrict env vars to a named scope prefix (e.g. APP_, DEV_, PROD_)."""

from typing import Dict, List, Optional


class ScopeError(Exception):
    """Raised when a scope operation fails."""


def extract_scope(env: Dict[str, str], scope: str, *, strip_prefix: bool = False) -> Dict[str, str]:
    """Return only keys that belong to the given scope prefix.

    Args:
        env: The source env mapping.
        scope: The prefix to filter by (e.g. "APP"). A trailing underscore
               is added automatically if not present.
        strip_prefix: If True, remove the scope prefix from the returned keys.

    Returns:
        A new dict with matching key/value pairs.
    """
    prefix = scope.rstrip("_") + "_"
    result: Dict[str, str] = {}
    for key, value in env.items():
        if key.upper().startswith(prefix.upper()):
            new_key = key[len(prefix):] if strip_prefix else key
            result[new_key] = value
    return result


def inject_scope(env: Dict[str, str], scope: str) -> Dict[str, str]:
    """Return a new dict where every key is prefixed with the given scope.

    Keys that already carry the prefix are left unchanged.

    Args:
        env: The source env mapping.
        scope: The prefix to add (e.g. "APP").

    Returns:
        A new dict with all keys prefixed.
    """
    prefix = scope.rstrip("_") + "_"
    result: Dict[str, str] = {}
    for key, value in env.items():
        if key.upper().startswith(prefix.upper()):
            result[key] = value
        else:
            result[prefix + key] = value
    return result


def list_scopes(env: Dict[str, str]) -> List[str]:
    """Return a sorted list of distinct scope prefixes found in *env*.

    A scope prefix is the segment before the first underscore in a key.
    Keys without an underscore are ignored.
    """
    scopes: set = set()
    for key in env:
        if "_" in key:
            scopes.add(key.split("_", 1)[0].upper())
    return sorted(scopes)


def remove_scope(env: Dict[str, str], scope: str) -> Dict[str, str]:
    """Return a new dict with all keys belonging to *scope* removed."""
    prefix = scope.rstrip("_") + "_"
    return {k: v for k, v in env.items() if not k.upper().startswith(prefix.upper())}
