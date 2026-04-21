"""bouncer.py — Enforce allowed/blocked key policies on an env dict."""

from __future__ import annotations

import re
from typing import Dict, List, Optional


class BouncerError(Exception):
    """Raised when a policy violation cannot be auto-resolved."""


def _matches_any(key: str, patterns: List[str], case_sensitive: bool = False) -> bool:
    flags = 0 if case_sensitive else re.IGNORECASE
    return any(re.fullmatch(p, key, flags=flags) for p in patterns)


def check_allowlist(
    env: Dict[str, str],
    patterns: List[str],
    *,
    case_sensitive: bool = False,
) -> List[str]:
    """Return keys that do NOT match any allowlist pattern."""
    return [
        k for k in env
        if not _matches_any(k, patterns, case_sensitive=case_sensitive)
    ]


def check_blocklist(
    env: Dict[str, str],
    patterns: List[str],
    *,
    case_sensitive: bool = False,
) -> List[str]:
    """Return keys that match at least one blocklist pattern."""
    return [
        k for k in env
        if _matches_any(k, patterns, case_sensitive=case_sensitive)
    ]


def enforce_allowlist(
    env: Dict[str, str],
    patterns: List[str],
    *,
    case_sensitive: bool = False,
    raise_on_violation: bool = False,
) -> Dict[str, str]:
    """Return a copy of *env* containing only allowlisted keys.

    If *raise_on_violation* is True and any key is rejected, raise BouncerError.
    """
    rejected = check_allowlist(env, patterns, case_sensitive=case_sensitive)
    if raise_on_violation and rejected:
        raise BouncerError(
            f"Keys not in allowlist: {', '.join(sorted(rejected))}"
        )
    return {k: v for k, v in env.items() if k not in rejected}


def enforce_blocklist(
    env: Dict[str, str],
    patterns: List[str],
    *,
    case_sensitive: bool = False,
    raise_on_violation: bool = False,
) -> Dict[str, str]:
    """Return a copy of *env* with blocklisted keys removed.

    If *raise_on_violation* is True and any key is matched, raise BouncerError.
    """
    blocked = check_blocklist(env, patterns, case_sensitive=case_sensitive)
    if raise_on_violation and blocked:
        raise BouncerError(
            f"Blocked keys present: {', '.join(sorted(blocked))}"
        )
    return {k: v for k, v in env.items() if k not in blocked}


def get_policy_violations(
    env: Dict[str, str],
    allowlist: Optional[List[str]] = None,
    blocklist: Optional[List[str]] = None,
    *,
    case_sensitive: bool = False,
) -> Dict[str, List[str]]:
    """Return a dict with 'not_allowed' and 'blocked' violation lists."""
    return {
        "not_allowed": check_allowlist(env, allowlist or [], case_sensitive=case_sensitive)
        if allowlist else [],
        "blocked": check_blocklist(env, blocklist or [], case_sensitive=case_sensitive)
        if blocklist else [],
    }
