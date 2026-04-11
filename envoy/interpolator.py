"""Variable interpolation for .env files.

Supports ${VAR} and $VAR style references within values.
"""

import re
from typing import Dict, List, Optional

_BRACE_REF = re.compile(r'\$\{([A-Za-z_][A-Za-z0-9_]*)\}')
_BARE_REF = re.compile(r'\$([A-Za-z_][A-Za-z0-9_]*)')


class InterpolationError(Exception):
    """Raised when interpolation fails (e.g. circular or missing reference)."""


def _resolve_value(
    key: str,
    env: Dict[str, str],
    resolved: Dict[str, str],
    visiting: set,
    strict: bool,
) -> str:
    if key in resolved:
        return resolved[key]
    if key in visiting:
        raise InterpolationError(f"Circular reference detected for key: '{key}'")
    if key not in env:
        if strict:
            raise InterpolationError(f"Undefined variable referenced: '{key}'")
        return f"${{{key}}}"

    visiting.add(key)
    raw = env[key]

    def replace_brace(m: re.Match) -> str:
        ref = m.group(1)
        return _resolve_value(ref, env, resolved, visiting, strict)

    def replace_bare(m: re.Match) -> str:
        ref = m.group(1)
        return _resolve_value(ref, env, resolved, visiting, strict)

    value = _BRACE_REF.sub(replace_brace, raw)
    value = _BARE_REF.sub(replace_bare, value)

    visiting.discard(key)
    resolved[key] = value
    return value


def interpolate_env(
    env: Dict[str, str],
    strict: bool = False,
    os_env: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """Return a new dict with all variable references expanded.

    Args:
        env: The parsed environment mapping.
        strict: If True, raise on undefined references; otherwise leave them.
        os_env: Optional fallback mapping (e.g. os.environ) for undefined refs.

    Returns:
        A new dict with interpolated values.
    """
    lookup: Dict[str, str] = {}
    if os_env:
        lookup.update(os_env)
    lookup.update(env)

    resolved: Dict[str, str] = {}
    visiting: set = set()

    for key in env:
        _resolve_value(key, lookup, resolved, visiting, strict)

    return {k: resolved[k] for k in env}


def find_references(env: Dict[str, str]) -> Dict[str, List[str]]:
    """Return a mapping of key -> list of variable names it references."""
    result: Dict[str, List[str]] = {}
    for key, value in env.items():
        refs = _BRACE_REF.findall(value) + _BARE_REF.findall(value)
        if refs:
            result[key] = refs
    return result
