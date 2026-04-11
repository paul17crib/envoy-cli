"""Inject env variables into the current process environment or a subprocess."""

from __future__ import annotations

import os
import subprocess
from typing import Dict, List, Optional


class InjectionError(Exception):
    """Raised when injection fails."""


def inject_into_os(env: Dict[str, str], *, overwrite: bool = True) -> List[str]:
    """Inject *env* into ``os.environ``.

    Returns a list of keys that were actually set.
    When *overwrite* is False, existing keys are skipped.
    """
    injected: List[str] = []
    for key, value in env.items():
        if not overwrite and key in os.environ:
            continue
        os.environ[key] = value
        injected.append(key)
    return injected


def build_env(env: Dict[str, str], *, inherit: bool = True) -> Dict[str, str]:
    """Build a full environment dict for subprocess use.

    If *inherit* is True the current process environment is used as the base
    and *env* values are layered on top.
    """
    base: Dict[str, str] = dict(os.environ) if inherit else {}
    base.update(env)
    return base


def run_with_env(
    command: List[str],
    env: Dict[str, str],
    *,
    inherit: bool = True,
    capture_output: bool = False,
    timeout: Optional[int] = None,
) -> subprocess.CompletedProcess:
    """Run *command* with *env* injected.

    Raises :class:`InjectionError` when the command list is empty.
    """
    if not command:
        raise InjectionError("command must not be empty")

    full_env = build_env(env, inherit=inherit)
    return subprocess.run(
        command,
        env=full_env,
        capture_output=capture_output,
        timeout=timeout,
    )


def keys_not_in_os(env: Dict[str, str]) -> List[str]:
    """Return keys from *env* that are not currently set in ``os.environ``."""
    return [k for k in env if k not in os.environ]
