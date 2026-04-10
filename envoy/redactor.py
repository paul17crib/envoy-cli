"""Redactor: replace sensitive values in env dicts with custom placeholders."""

from typing import Dict, Optional
from envoy.masker import is_sensitive_key

DEFAULT_PLACEHOLDER = "REDACTED"


def redact_env(
    env: Dict[str, str],
    placeholder: str = DEFAULT_PLACEHOLDER,
    custom_patterns: Optional[list] = None,
) -> Dict[str, str]:
    """Return a new dict with sensitive values replaced by *placeholder*.

    Unlike mask_env (which replaces with asterisks), redact_env replaces the
    entire value with a fixed placeholder string, making it safe to embed in
    logs, reports, or serialised output without leaking length information.
    """
    return {
        key: (placeholder if is_sensitive_key(key, custom_patterns) else value)
        for key, value in env.items()
    }


def redact_keys(
    env: Dict[str, str],
    keys: list,
    placeholder: str = DEFAULT_PLACEHOLDER,
) -> Dict[str, str]:
    """Return a new dict with *keys* explicitly replaced by *placeholder*.

    Useful when the caller already knows which keys to redact, regardless of
    whether they match the sensitive-key heuristics.
    """
    key_set = {k.upper() for k in keys}
    return {
        key: (placeholder if key.upper() in key_set else value)
        for key, value in env.items()
    }


def get_redacted_keys(
    env: Dict[str, str],
    placeholder: str = DEFAULT_PLACEHOLDER,
    custom_patterns: Optional[list] = None,
) -> list:
    """Return a sorted list of keys that would be redacted in *env*."""
    return sorted(
        key
        for key in env
        if is_sensitive_key(key, custom_patterns)
    )
