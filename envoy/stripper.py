"""Strip keys from an env dict based on various criteria."""

from __future__ import annotations

from typing import Dict, List, Optional
import re

Env = Dict[str, str]


class StripError(Exception):
    """Raised when stripping fails due to invalid input."""


def strip_keys(env: Env, keys: List[str], missing_ok: bool = False) -> Env:
    """Return a new env with the specified keys removed.

    Args:
        env: Source environment mapping.
        keys: Keys to remove.
        missing_ok: If False, raises StripError when a key is not found.

    Returns:
        New dict without the stripped keys.
    """
    if not keys:
        raise StripError("At least one key must be specified.")
    result = dict(env)
    for key in keys:
        if key not in result:
            if not missing_ok:
                raise StripError(f"Key not found: {key!r}")
        else:
            del result[key]
    return result


def strip_by_pattern(env: Env, pattern: str, case_sensitive: bool = False) -> Env:
    """Return a new env with keys matching *pattern* removed.

    Args:
        env: Source environment mapping.
        pattern: Regular-expression pattern tested against each key.
        case_sensitive: Whether the match is case-sensitive.

    Returns:
        New dict without the matched keys.
    """
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        compiled = re.compile(pattern, flags)
    except re.error as exc:
        raise StripError(f"Invalid pattern {pattern!r}: {exc}") from exc
    return {k: v for k, v in env.items() if not compiled.search(k)}


def strip_empty(env: Env) -> Env:
    """Return a new env with keys whose values are empty strings removed."""
    return {k: v for k, v in env.items() if v != ""}


def get_stripped_keys(original: Env, stripped: Env) -> List[str]:
    """Return the list of keys present in *original* but absent from *stripped*."""
    return [k for k in original if k not in stripped]
