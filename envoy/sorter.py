"""Key sorting utilities for .env files."""

from typing import Dict, List, Optional, Tuple


def sort_env(
    env: Dict[str, str],
    reverse: bool = False,
    case_sensitive: bool = False,
) -> Dict[str, str]:
    """Return a new dict with keys sorted alphabetically."""
    key_fn = (lambda k: k) if case_sensitive else (lambda k: k.lower())
    sorted_keys = sorted(env.keys(), key=key_fn, reverse=reverse)
    return {k: env[k] for k in sorted_keys}


def sort_by_value(
    env: Dict[str, str],
    reverse: bool = False,
    case_sensitive: bool = False,
) -> Dict[str, str]:
    """Return a new dict sorted by value."""
    key_fn = (lambda item: item[1]) if case_sensitive else (lambda item: item[1].lower())
    sorted_items = sorted(env.items(), key=key_fn, reverse=reverse)
    return dict(sorted_items)


def sort_by_length(
    env: Dict[str, str],
    reverse: bool = False,
) -> Dict[str, str]:
    """Return a new dict sorted by key length."""
    sorted_keys = sorted(env.keys(), key=len, reverse=reverse)
    return {k: env[k] for k in sorted_keys}


def group_sort(
    env: Dict[str, str],
    delimiter: str = "_",
    reverse: bool = False,
) -> Dict[str, str]:
    """Sort keys grouping by prefix (portion before first delimiter)."""
    def group_key(k: str) -> Tuple[str, str]:
        parts = k.split(delimiter, 1)
        prefix = parts[0].lower()
        rest = parts[1].lower() if len(parts) > 1 else ""
        return (prefix, rest)

    sorted_keys = sorted(env.keys(), key=group_key, reverse=reverse)
    return {k: env[k] for k in sorted_keys}


def get_sort_order(env: Dict[str, str]) -> List[str]:
    """Return the current key order as a list."""
    return list(env.keys())
