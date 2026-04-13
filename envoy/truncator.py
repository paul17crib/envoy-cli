"""Truncate or limit env values by length constraints."""

from __future__ import annotations

from typing import Optional


class TruncateError(ValueError):
    pass


def truncate_env(
    env: dict[str, str],
    max_length: int,
    suffix: str = "...",
    keys: Optional[list[str]] = None,
) -> dict[str, str]:
    """Return a new env with values truncated to max_length.

    Args:
        env: Source environment dict.
        max_length: Maximum allowed value length (including suffix).
        suffix: String appended to truncated values.
        keys: Optional list of keys to restrict truncation to.

    Raises:
        TruncateError: If max_length is too small to fit the suffix.
    """
    if max_length < len(suffix):
        raise TruncateError(
            f"max_length ({max_length}) must be >= suffix length ({len(suffix)})"
        )

    result: dict[str, str] = {}
    for key, value in env.items():
        if keys is not None and key not in keys:
            result[key] = value
            continue
        if len(value) > max_length:
            cut = max_length - len(suffix)
            result[key] = value[:cut] + suffix
        else:
            result[key] = value
    return result


def get_truncated_keys(
    env: dict[str, str],
    max_length: int,
    keys: Optional[list[str]] = None,
) -> list[str]:
    """Return keys whose values exceed max_length."""
    target = keys if keys is not None else list(env.keys())
    return [k for k in target if k in env and len(env[k]) > max_length]


def pad_env(
    env: dict[str, str],
    min_length: int,
    pad_char: str = " ",
    align: str = "left",
    keys: Optional[list[str]] = None,
) -> dict[str, str]:
    """Return a new env with values padded to at least min_length.

    Args:
        env: Source environment dict.
        min_length: Minimum value length.
        pad_char: Character used for padding (single char).
        align: 'left' pads on right, 'right' pads on left, 'center' both sides.
        keys: Optional list of keys to restrict padding to.

    Raises:
        TruncateError: If pad_char is not a single character.
    """
    if len(pad_char) != 1:
        raise TruncateError("pad_char must be a single character")
    if align not in ("left", "right", "center"):
        raise TruncateError("align must be 'left', 'right', or 'center'")

    result: dict[str, str] = {}
    for key, value in env.items():
        if keys is not None and key not in keys:
            result[key] = value
            continue
        if len(value) >= min_length:
            result[key] = value
        elif align == "left":
            result[key] = value.ljust(min_length, pad_char)
        elif align == "right":
            result[key] = value.rjust(min_length, pad_char)
        else:
            result[key] = value.center(min_length, pad_char)
    return result
