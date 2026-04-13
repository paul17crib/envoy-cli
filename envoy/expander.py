"""Expander: expand environment variable references within .env values.

Supports ${VAR} and $VAR syntax, with optional fallback defaults via ${VAR:-default}.
"""

from __future__ import annotations

import re
from typing import Optional

_BRACE_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-(.*?))?\}")
_BARE_RE = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")


class ExpansionError(Exception):
    """Raised when a required variable reference cannot be resolved."""


def expand_value(
    value: str,
    env: dict[str, str],
    *,
    strict: bool = False,
) -> str:
    """Expand all variable references in *value* using *env*.

    Args:
        value:  The raw string that may contain ``$VAR`` or ``${VAR}`` refs.
        env:    Mapping used to resolve references.
        strict: If True, raise :class:`ExpansionError` for undefined refs.
                Otherwise leave the reference token in-place.

    Returns:
        The expanded string.
    """

    def _replace_brace(m: re.Match) -> str:  # type: ignore[type-arg]
        key, default = m.group(1), m.group(2)
        if key in env:
            return env[key]
        if default is not None:
            return default
        if strict:
            raise ExpansionError(f"Undefined variable reference: {key!r}")
        return m.group(0)

    def _replace_bare(m: re.Match) -> str:  # type: ignore[type-arg]
        key = m.group(1)
        if key in env:
            return env[key]
        if strict:
            raise ExpansionError(f"Undefined variable reference: {key!r}")
        return m.group(0)

    result = _BRACE_RE.sub(_replace_brace, value)
    result = _BARE_RE.sub(_replace_bare, result)
    return result


def expand_env(
    env: dict[str, str],
    *,
    strict: bool = False,
    extra: Optional[dict[str, str]] = None,
) -> dict[str, str]:
    """Return a new dict with all values expanded in-order.

    Earlier keys are resolved before later ones, so chained references work
    as long as they are declared first.

    Args:
        env:    Source environment mapping.
        strict: Propagated to :func:`expand_value`.
        extra:  Additional variables available for resolution but not included
                in the output (e.g. OS environment overrides).

    Returns:
        New dict with expanded values.
    """
    lookup: dict[str, str] = dict(extra or {})
    result: dict[str, str] = {}
    for key, raw in env.items():
        expanded = expand_value(raw, lookup, strict=strict)
        result[key] = expanded
        lookup[key] = expanded
    return result


def get_expanded_keys(original: dict[str, str], expanded: dict[str, str]) -> list[str]:
    """Return list of keys whose values changed after expansion."""
    return [k for k in original if original.get(k) != expanded.get(k)]
