"""censor.py — Selectively blank or replace env values based on key patterns."""

from __future__ import annotations

import re
from typing import Dict, List, Optional

from envoy.masker import is_sensitive_key

CENSOR_PLACEHOLDER = "[CENSORED]"


class CensorError(Exception):
    """Raised when censoring fails due to invalid input."""


def censor_value(value: str, placeholder: str = CENSOR_PLACEHOLDER) -> str:
    """Return the placeholder string regardless of value."""
    return placeholder


def censor_env(
    env: Dict[str, str],
    *,
    keys: Optional[List[str]] = None,
    patterns: Optional[List[str]] = None,
    sensitive_only: bool = False,
    placeholder: str = CENSOR_PLACEHOLDER,
) -> Dict[str, str]:
    """Return a copy of *env* with selected values replaced by *placeholder*.

    Selection priority (any match triggers censoring):
    1. Explicit *keys* list.
    2. Regex *patterns* matched against key names.
    3. *sensitive_only* flag — censor keys detected by :func:`is_sensitive_key`.

    If none of the selectors are provided every value is censored.
    """
    if patterns is not None:
        try:
            compiled = [re.compile(p, re.IGNORECASE) for p in patterns]
        except re.error as exc:
            raise CensorError(f"Invalid pattern: {exc}") from exc
    else:
        compiled = []

    explicit = set(keys or [])
    result: Dict[str, str] = {}

    no_selector = not keys and not patterns and not sensitive_only

    for k, v in env.items():
        if no_selector:
            result[k] = placeholder
        elif k in explicit:
            result[k] = placeholder
        elif any(rx.search(k) for rx in compiled):
            result[k] = placeholder
        elif sensitive_only and is_sensitive_key(k):
            result[k] = placeholder
        else:
            result[k] = v

    return result


def get_censored_keys(
    env: Dict[str, str],
    censored: Dict[str, str],
    placeholder: str = CENSOR_PLACEHOLDER,
) -> List[str]:
    """Return the list of keys whose values differ between *env* and *censored*."""
    return [k for k in env if censored.get(k) == placeholder and env[k] != placeholder]
