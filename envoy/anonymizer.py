"""Anonymize env values by replacing them with deterministic or random placeholders."""

from __future__ import annotations

import hashlib
import re
import secrets
from typing import Dict, Optional


class AnonymizerError(Exception):
    pass


_PLACEHOLDER_RE = re.compile(r'^[A-Z0-9_]+$')


def _hash_value(value: str, salt: str) -> str:
    """Return a short deterministic hex string derived from value + salt."""
    raw = hashlib.sha256(f"{salt}:{value}".encode()).hexdigest()
    return raw[:16]


def anonymize_value(
    value: str,
    *,
    mode: str = "hash",
    salt: str = "envoy",
    length: int = 16,
) -> str:
    """Return an anonymized version of *value*.

    Modes:
      - ``hash``   – deterministic SHA-256-derived hex string (default)
      - ``random`` – cryptographically random hex string
      - ``blank``  – empty string
    """
    if mode == "hash":
        return _hash_value(value, salt)
    if mode == "random":
        return secrets.token_hex(length // 2)
    if mode == "blank":
        return ""
    raise AnonymizerError(f"Unknown anonymization mode: {mode!r}")


def anonymize_env(
    env: Dict[str, str],
    *,
    keys: Optional[list] = None,
    mode: str = "hash",
    salt: str = "envoy",
    length: int = 16,
) -> Dict[str, str]:
    """Return a new env dict with selected (or all) values anonymized.

    Args:
        env:    Source environment mapping.
        keys:   Explicit list of keys to anonymize; ``None`` means all.
        mode:   Anonymization mode passed to :func:`anonymize_value`.
        salt:   Salt used in ``hash`` mode.
        length: Token length used in ``random`` mode.

    Returns:
        A new dict; the original is never mutated.
    """
    target = set(keys) if keys is not None else set(env)
    unknown = target - set(env)
    if unknown:
        raise AnonymizerError(f"Keys not found in env: {sorted(unknown)}")

    result = dict(env)
    for key in target:
        result[key] = anonymize_value(env[key], mode=mode, salt=salt, length=length)
    return result


def get_anonymized_keys(
    original: Dict[str, str],
    anonymized: Dict[str, str],
) -> list:
    """Return keys whose values differ between *original* and *anonymized*."""
    return [k for k in original if original.get(k) != anonymized.get(k)]
