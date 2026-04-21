"""Pad or align env values to a consistent width for display or export."""

from __future__ import annotations

from typing import Dict, List, Optional


class PadderError(Exception):
    """Raised when padding cannot be applied."""


def _max_key_length(env: Dict[str, str], keys: Optional[List[str]] = None) -> int:
    """Return the length of the longest key in *env* (or subset *keys*)."""
    target = keys if keys is not None else list(env.keys())
    if not target:
        return 0
    return max(len(k) for k in target if k in env)


def _max_value_length(env: Dict[str, str], keys: Optional[List[str]] = None) -> int:
    """Return the length of the longest value in *env* (or subset *keys*)."""
    target = keys if keys is not None else list(env.keys())
    if not target:
        return 0
    return max(len(env[k]) for k in target if k in env)


def pad_keys(
    env: Dict[str, str],
    width: Optional[int] = None,
    fill: str = " ",
    keys: Optional[List[str]] = None,
) -> Dict[str, str]:
    """Return a new env dict with keys right-padded to *width* (or auto).

    Only keys listed in *keys* are padded; others pass through unchanged.
    """
    if len(fill) != 1:
        raise PadderError("fill must be exactly one character")
    target = set(keys) if keys is not None else set(env.keys())
    effective_width = width if width is not None else _max_key_length(env, list(target))
    result: Dict[str, str] = {}
    for k, v in env.items():
        if k in target:
            result[k.ljust(effective_width, fill)] = v
        else:
            result[k] = v
    return result


def pad_values(
    env: Dict[str, str],
    width: Optional[int] = None,
    fill: str = " ",
    align: str = "left",
    keys: Optional[List[str]] = None,
) -> Dict[str, str]:
    """Return a new env dict with values padded to *width* (or auto).

    *align* controls padding side: 'left' (right-pad) or 'right' (left-pad).
    Only keys listed in *keys* are affected; others pass through unchanged.
    """
    if len(fill) != 1:
        raise PadderError("fill must be exactly one character")
    if align not in ("left", "right"):
        raise PadderError("align must be 'left' or 'right'")
    target = set(keys) if keys is not None else set(env.keys())
    effective_width = width if width is not None else _max_value_length(env, list(target))
    result: Dict[str, str] = {}
    for k, v in env.items():
        if k in target:
            result[k] = v.ljust(effective_width, fill) if align == "left" else v.rjust(effective_width, fill)
        else:
            result[k] = v
    return result


def get_padded_keys(
    original: Dict[str, str],
    padded: Dict[str, str],
) -> List[str]:
    """Return list of keys whose values differ between *original* and *padded*."""
    return [k for k in padded if padded.get(k) != original.get(k)]
