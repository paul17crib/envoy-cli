"""stringer.py — Utilities for transforming env values as formatted strings."""

from __future__ import annotations

import re
from typing import Dict, List, Optional


class StringerError(Exception):
    """Raised when a string operation cannot be completed."""


_TRUNCATE_SUFFIX = "..."


def truncate_value(value: str, max_length: int, suffix: str = _TRUNCATE_SUFFIX) -> str:
    """Truncate *value* to *max_length* characters, appending *suffix* if cut."""
    if max_length < len(suffix):
        raise StringerError(
            f"max_length ({max_length}) must be >= suffix length ({len(suffix)})"
        )
    if len(value) <= max_length:
        return value
    return value[: max_length - len(suffix)] + suffix


def pad_value(value: str, width: int, align: str = "left", char: str = " ") -> str:
    """Pad *value* to *width* using *char*.  align: 'left' | 'right' | 'center'."""
    if align == "left":
        return value.ljust(width, char)
    if align == "right":
        return value.rjust(width, char)
    if align == "center":
        return value.center(width, char)
    raise StringerError(f"Unknown align value: {align!r}. Use 'left', 'right', or 'center'.")


def slugify_value(value: str, separator: str = "-") -> str:
    """Convert *value* to a lowercase slug using *separator*."""
    value = value.lower().strip()
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"[\s_]+", separator, value)
    value = re.sub(rf"{re.escape(separator)}+", separator, value)
    return value.strip(separator)


def wrap_value(value: str, prefix: str = "", suffix: str = "") -> str:
    """Wrap *value* with *prefix* and *suffix*."""
    return f"{prefix}{value}{suffix}"


def string_env(
    env: Dict[str, str],
    *,
    operation: str,
    keys: Optional[List[str]] = None,
    **kwargs,
) -> Dict[str, str]:
    """Apply a string *operation* to *env* values, optionally restricted to *keys*.

    Supported operations: 'truncate', 'pad', 'slugify', 'wrap'.
    Extra keyword arguments are forwarded to the underlying operation function.
    Returns a new dict; the original is not mutated.
    """
    ops = {
        "truncate": truncate_value,
        "pad": pad_value,
        "slugify": slugify_value,
        "wrap": wrap_value,
    }
    if operation not in ops:
        raise StringerError(
            f"Unknown operation {operation!r}. Choose from: {', '.join(ops)}"
        )
    fn = ops[operation]
    target_keys = set(keys) if keys else set(env.keys())
    result = dict(env)
    for k in target_keys:
        if k in result:
            result[k] = fn(result[k], **kwargs)
    return result


def get_stringed_keys(
    original: Dict[str, str], updated: Dict[str, str]
) -> List[str]:
    """Return keys whose values changed between *original* and *updated*."""
    return [k for k in updated if original.get(k) != updated.get(k)]
