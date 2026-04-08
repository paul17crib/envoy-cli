"""Sync .env files between local and remote environments."""

import os
import json
from pathlib import Path
from typing import Optional

from envoy.parser import parse_env_file, parse_env_string, serialize_env


class SyncError(Exception):
    """Raised when a sync operation fails."""
    pass


def load_local(path: str) -> dict:
    """Load environment variables from a local .env file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Local env file not found: {path}")
    return parse_env_file(str(p))


def save_local(env: dict, path: str, overwrite: bool = False) -> None:
    """Save environment variables to a local .env file."""
    p = Path(path)
    if p.exists() and not overwrite:
        raise SyncError(f"File already exists: {path}. Use overwrite=True to replace.")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(serialize_env(env))


def merge_envs(base: dict, override: dict, strategy: str = "override") -> dict:
    """Merge two env dicts.

    Strategies:
        - 'override': override keys from base with values from override
        - 'keep': keep base values if key already exists
        - 'union': include all keys from both, prefer override on conflict
    """
    if strategy == "keep":
        merged = dict(override)
        merged.update({k: v for k, v in base.items() if k not in merged})
        return merged
    elif strategy in ("override", "union"):
        merged = dict(base)
        merged.update(override)
        return merged
    else:
        raise ValueError(f"Unknown merge strategy: {strategy!r}")


def diff_envs(local: dict, remote: dict) -> dict:
    """Return a diff summary between local and remote env dicts."""
    local_keys = set(local)
    remote_keys = set(remote)

    added = {k: remote[k] for k in remote_keys - local_keys}
    removed = {k: local[k] for k in local_keys - remote_keys}
    changed = {
        k: {"local": local[k], "remote": remote[k]}
        for k in local_keys & remote_keys
        if local[k] != remote[k]
    }
    unchanged = {
        k: local[k]
        for k in local_keys & remote_keys
        if local[k] == remote[k]
    }

    return {
        "added": added,
        "removed": removed,
        "changed": changed,
        "unchanged": unchanged,
    }
