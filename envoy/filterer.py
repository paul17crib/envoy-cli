"""Filter .env entries by key patterns, value patterns, or sensitivity."""

from __future__ import annotations

import re
from typing import Dict, List, Optional

from envoy.masker import is_sensitive_key


def filter_by_key_pattern(
    env: Dict[str, str],
    pattern: str,
    case_sensitive: bool = False,
) -> Dict[str, str]:
    """Return entries whose keys match the given regex pattern."""
    flags = 0 if case_sensitive else re.IGNORECASE
    compiled = re.compile(pattern, flags)
    return {k: v for k, v in env.items() if compiled.search(k)}


def filter_by_value_pattern(
    env: Dict[str, str],
    pattern: str,
    case_sensitive: bool = False,
) -> Dict[str, str]:
    """Return entries whose values match the given regex pattern."""
    flags = 0 if case_sensitive else re.IGNORECASE
    compiled = re.compile(pattern, flags)
    return {k: v for k, v in env.items() if compiled.search(v)}


def filter_sensitive(
    env: Dict[str, str],
    extra_patterns: Optional[List[str]] = None,
) -> Dict[str, str]:
    """Return only entries whose keys are considered sensitive."""
    return {
        k: v
        for k, v in env.items()
        if is_sensitive_key(k, extra_patterns=extra_patterns)
    }


def filter_non_sensitive(
    env: Dict[str, str],
    extra_patterns: Optional[List[str]] = None,
) -> Dict[str, str]:
    """Return only entries whose keys are NOT considered sensitive."""
    return {
        k: v
        for k, v in env.items()
        if not is_sensitive_key(k, extra_patterns=extra_patterns)
    }


def filter_empty(env: Dict[str, str]) -> Dict[str, str]:
    """Return only entries with empty string values."""
    return {k: v for k, v in env.items() if v == ""}


def filter_non_empty(env: Dict[str, str]) -> Dict[str, str]:
    """Return only entries with non-empty string values."""
    return {k: v for k, v in env.items() if v != ""}


def exclude_keys(
    env: Dict[str, str],
    keys: List[str],
    case_sensitive: bool = True,
) -> Dict[str, str]:
    """Return env without the specified keys."""
    if case_sensitive:
        exclude = set(keys)
        return {k: v for k, v in env.items() if k not in exclude}
    exclude_lower = {k.lower() for k in keys}
    return {k: v for k, v in env.items() if k.lower() not in exclude_lower}
