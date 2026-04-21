"""clamper.py — Clamp env values to a min/max length range, optionally truncating or padding."""

from __future__ import annotations

from typing import Dict, List, Optional


class ClamperError(Exception):
    """Raised when clamping parameters are invalid."""


def _validate_range(min_len: int, max_len: int) -> None:
    if min_len < 0:
        raise ClamperError(f"min_len must be >= 0, got {min_len}")
    if max_len < 1:
        raise ClamperError(f"max_len must be >= 1, got {max_len}")
    if min_len > max_len:
        raise ClamperError(
            f"min_len ({min_len}) must not exceed max_len ({max_len})"
        )


def clamp_value(
    value: str,
    min_len: int = 0,
    max_len: int = 255,
    pad_char: str = " ",
    truncate_suffix: str = "",
) -> str:
    """Return *value* clamped so that min_len <= len(result) <= max_len.

    - Values longer than max_len are truncated; *truncate_suffix* is appended
      (and counts toward max_len).
    - Values shorter than min_len are right-padded with *pad_char*.
    """
    _validate_range(min_len, max_len)
    if len(pad_char) != 1:
        raise ClamperError("pad_char must be exactly one character")
    if len(truncate_suffix) >= max_len:
        raise ClamperError(
            "truncate_suffix length must be less than max_len"
        )

    if len(value) > max_len:
        cut = max_len - len(truncate_suffix)
        value = value[:cut] + truncate_suffix

    if len(value) < min_len:
        value = value.ljust(min_len, pad_char)

    return value


def clamp_env(
    env: Dict[str, str],
    min_len: int = 0,
    max_len: int = 255,
    keys: Optional[List[str]] = None,
    pad_char: str = " ",
    truncate_suffix: str = "",
) -> Dict[str, str]:
    """Return a new env dict with values clamped to [min_len, max_len].

    If *keys* is provided only those keys are processed; others pass through.
    """
    _validate_range(min_len, max_len)
    target = set(keys) if keys is not None else set(env.keys())
    return {
        k: (
            clamp_value(v, min_len, max_len, pad_char, truncate_suffix)
            if k in target
            else v
        )
        for k, v in env.items()
    }


def get_clamped_keys(
    original: Dict[str, str], clamped: Dict[str, str]
) -> List[str]:
    """Return list of keys whose values changed after clamping."""
    return [k for k in original if original[k] != clamped.get(k, original[k])]
