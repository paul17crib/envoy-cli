"""Select a subset of keys from an env dict based on various criteria."""

from __future__ import annotations

import re
from typing import Dict, List, Optional

Env = Dict[str, str]


class SelectorError(Exception):
    """Raised when selection criteria are invalid."""


def select_keys(env: Env, keys: List[str], missing_ok: bool = False) -> Env:
    """Return a new env containing only the specified keys."""
    result: Env = {}
    for key in keys:
        if key in env:
            result[key] = env[key]
        elif not missing_ok:
            raise SelectorError(f"Key not found: {key!r}")
    return result


def select_by_pattern(env: Env, pattern: str, case_sensitive: bool = False) -> Env:
    """Return keys whose names match *pattern* (regex)."""
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        rx = re.compile(pattern, flags)
    except re.error as exc:
        raise SelectorError(f"Invalid regex pattern: {exc}") from exc
    return {k: v for k, v in env.items() if rx.search(k)}


def select_by_value_pattern(env: Env, pattern: str, case_sensitive: bool = False) -> Env:
    """Return keys whose values match *pattern* (regex)."""
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        rx = re.compile(pattern, flags)
    except re.error as exc:
        raise SelectorError(f"Invalid regex pattern: {exc}") from exc
    return {k: v for k, v in env.items() if rx.search(v)}


def select_first(env: Env, n: int) -> Env:
    """Return the first *n* keys (insertion order)."""
    if n < 0:
        raise SelectorError("n must be >= 0")
    return dict(list(env.items())[:n])


def select_last(env: Env, n: int) -> Env:
    """Return the last *n* keys (insertion order)."""
    if n < 0:
        raise SelectorError("n must be >= 0")
    items = list(env.items())
    return dict(items[-n:] if n else [])


def get_selected_keys(env: Env, selected: Env) -> List[str]:
    """Return sorted list of keys that were selected."""
    return sorted(selected.keys())
