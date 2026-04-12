"""substitutor.py — Replace values in an env dict using a mapping or pattern."""

from __future__ import annotations

import re
from typing import Dict, Optional


class SubstitutionError(Exception):
    """Raised when a substitution cannot be applied."""


def substitute_value(
    value: str,
    find: str,
    replace: str,
    *,
    regex: bool = False,
    case_sensitive: bool = True,
) -> str:
    """Return *value* with occurrences of *find* replaced by *replace*."""
    if regex:
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            return re.sub(find, replace, value, flags=flags)
        except re.error as exc:
            raise SubstitutionError(f"Invalid regex pattern {find!r}: {exc}") from exc
    if not case_sensitive:
        pattern = re.compile(re.escape(find), re.IGNORECASE)
        return pattern.sub(replace, value)
    return value.replace(find, replace)


def substitute_env(
    env: Dict[str, str],
    find: str,
    replace: str,
    *,
    keys: Optional[list] = None,
    regex: bool = False,
    case_sensitive: bool = True,
) -> Dict[str, str]:
    """Return a new env dict with substitutions applied to values.

    Args:
        env: Source environment mapping.
        find: Substring or regex pattern to find.
        replace: Replacement string.
        keys: If given, only substitute in these keys.
        regex: Treat *find* as a regular expression.
        case_sensitive: Whether matching is case-sensitive.

    Returns:
        New dict with substituted values; original is not mutated.
    """
    result: Dict[str, str] = {}
    target_keys = set(keys) if keys is not None else None
    for k, v in env.items():
        if target_keys is None or k in target_keys:
            result[k] = substitute_value(v, find, replace, regex=regex, case_sensitive=case_sensitive)
        else:
            result[k] = v
    return result


def get_substituted_keys(
    original: Dict[str, str],
    updated: Dict[str, str],
) -> list:
    """Return list of keys whose values changed between *original* and *updated*."""
    return [k for k in original if original.get(k) != updated.get(k)]
