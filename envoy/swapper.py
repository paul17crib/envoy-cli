"""Swap keys or values between two env dicts."""

from __future__ import annotations

from typing import Dict, Optional

Env = Dict[str, str]


class SwapError(Exception):
    """Raised when a swap operation cannot be completed."""


def swap_keys(env: Env, key_a: str, key_b: str) -> Env:
    """Return a new env with the values of key_a and key_b exchanged."""
    if key_a not in env:
        raise SwapError(f"Key not found: {key_a!r}")
    if key_b not in env:
        raise SwapError(f"Key not found: {key_b!r}")
    result = dict(env)
    result[key_a], result[key_b] = env[key_b], env[key_a]
    return result


def swap_names(env: Env, key_a: str, key_b: str) -> Env:
    """Return a new env with key_a renamed to key_b and vice-versa.

    The values stay with their original keys; only the names are exchanged.
    """
    if key_a not in env:
        raise SwapError(f"Key not found: {key_a!r}")
    if key_b not in env:
        raise SwapError(f"Key not found: {key_b!r}")
    result = {}
    for k, v in env.items():
        if k == key_a:
            result[key_b] = v
        elif k == key_b:
            result[key_a] = v
        else:
            result[k] = v
    return result


def swap_with_default(
    env: Env,
    key_a: str,
    key_b: str,
    default: Optional[str] = "",
) -> Env:
    """Swap values between key_a and key_b, creating missing keys with *default*."""
    result = dict(env)
    val_a = env.get(key_a, default)
    val_b = env.get(key_b, default)
    result[key_a] = val_b
    result[key_b] = val_a
    return result


def get_swap_preview(env: Env, key_a: str, key_b: str) -> Dict[str, Dict[str, str]]:
    """Return a preview dict showing before/after values for both keys."""
    return {
        key_a: {"before": env.get(key_a, ""), "after": env.get(key_b, "")},
        key_b: {"before": env.get(key_b, ""), "after": env.get(key_a, "")},
    }
