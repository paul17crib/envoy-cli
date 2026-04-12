"""Aliaser: create and resolve short aliases for .env keys."""

from __future__ import annotations

from typing import Dict, Optional


class AliasError(Exception):
    """Raised when an alias operation fails."""


def add_alias(
    env: Dict[str, str],
    alias: str,
    target: str,
    overwrite: bool = False,
) -> Dict[str, str]:
    """Return a new env dict with *alias* pointing to the value of *target*.

    Raises AliasError if *target* is not present, if *alias* already exists
    and *overwrite* is False, or if *alias* == *target*.
    """
    if alias == target:
        raise AliasError(f"Alias and target must differ: '{alias}'")
    if target not in env:
        raise AliasError(f"Target key '{target}' not found in env")
    if alias in env and not overwrite:
        raise AliasError(
            f"Key '{alias}' already exists; use overwrite=True to replace it"
        )
    result = dict(env)
    result[alias] = env[target]
    return result


def remove_alias(
    env: Dict[str, str],
    alias: str,
) -> Dict[str, str]:
    """Return a new env dict with *alias* removed.

    Raises AliasError if *alias* is not present.
    """
    if alias not in env:
        raise AliasError(f"Key '{alias}' not found in env")
    result = dict(env)
    del result[alias]
    return result


def resolve_aliases(
    env: Dict[str, str],
    alias_map: Dict[str, str],
) -> Dict[str, str]:
    """Return a new env dict where every key listed in *alias_map* is replaced
    by its canonical name.

    *alias_map* maps ``alias -> canonical``.  If the canonical key already
    exists in *env* the alias value is **not** copied (canonical wins).
    Keys in *alias_map* that are absent from *env* are silently skipped.
    """
    result = dict(env)
    for alias, canonical in alias_map.items():
        if alias in result and canonical not in result:
            result[canonical] = result.pop(alias)
        elif alias in result and canonical in result:
            # canonical already present — just drop the alias
            del result[alias]
    return result


def list_aliases(
    env: Dict[str, str],
    alias_map: Dict[str, str],
) -> Dict[str, str]:
    """Return a mapping of ``alias -> value`` for every alias present in *env*."""
    return {alias: env[alias] for alias in alias_map if alias in env}
