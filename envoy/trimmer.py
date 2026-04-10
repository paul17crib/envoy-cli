"""Trimmer: remove keys from an env dict based on prefix, suffix, or pattern."""

from __future__ import annotations

import re
from typing import Dict, List, Optional


def trim_by_prefix(env: Dict[str, str], prefix: str, case_sensitive: bool = False) -> Dict[str, str]:
    """Return a copy of env with all keys matching the given prefix removed."""
    if not case_sensitive:
        prefix = prefix.upper()
    return {
        k: v for k, v in env.items()
        if not (k.upper() if not case_sensitive else k).startswith(prefix)
    }


def trim_by_suffix(env: Dict[str, str], suffix: str, case_sensitive: bool = False) -> Dict[str, str]:
    """Return a copy of env with all keys matching the given suffix removed."""
    if not case_sensitive:
        suffix = suffix.upper()
    return {
        k: v for k, v in env.items()
        if not (k.upper() if not case_sensitive else k).endswith(suffix)
    }


def trim_by_pattern(env: Dict[str, str], pattern: str) -> Dict[str, str]:
    """Return a copy of env with all keys matching the regex pattern removed."""
    compiled = re.compile(pattern)
    return {k: v for k, v in env.items() if not compiled.search(k)}


def trim_keys(env: Dict[str, str], keys: List[str]) -> Dict[str, str]:
    """Return a copy of env with the specified keys removed."""
    keys_set = set(keys)
    return {k: v for k, v in env.items() if k not in keys_set}


def get_trimmed_keys(
    original: Dict[str, str],
    trimmed: Dict[str, str],
) -> List[str]:
    """Return the list of keys that were removed during trimming."""
    return [k for k in original if k not in trimmed]
