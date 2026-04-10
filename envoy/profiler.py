"""Profile management: load and switch between named env profiles."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

from envoy.parser import parse_env_file, serialize_env
from envoy.sync import SyncError


DEFAULT_PROFILE = "default"


def profile_path(base: str, profile: str) -> Path:
    """Return the file path for a given profile name.

    The default profile maps to the base path itself; others use
    '.env.<profile>' convention.
    """
    p = Path(base)
    if profile == DEFAULT_PROFILE:
        return p
    return p.parent / f"{p.name}.{profile}"


def list_profiles(base: str) -> List[str]:
    """Return all profile names discovered alongside the base env file."""
    p = Path(base)
    profiles: List[str] = []
    if p.exists():
        profiles.append(DEFAULT_PROFILE)
    for sibling in sorted(p.parent.iterdir()):
        if sibling.name.startswith(f"{p.name}.") and sibling.is_file():
            suffix = sibling.name[len(p.name) + 1 :]
            if suffix:
                profiles.append(suffix)
    return profiles


def load_profile(base: str, profile: str) -> Dict[str, str]:
    """Load and return the env dict for the given profile."""
    path = profile_path(base, profile)
    if not path.exists():
        raise SyncError(f"Profile '{profile}' not found at {path}")
    return parse_env_file(str(path))


def save_profile(
    base: str,
    profile: str,
    env: Dict[str, str],
    overwrite: bool = True,
) -> Path:
    """Serialize and write *env* to the profile file, returning its path."""
    path = profile_path(base, profile)
    if path.exists() and not overwrite:
        raise SyncError(f"Profile file '{path}' already exists. Use overwrite=True to replace.")
    path.write_text(serialize_env(env), encoding="utf-8")
    return path


def active_profile(base: str) -> Optional[str]:
    """Return the name stored in '<base>.active', or None if unset."""
    marker = Path(base + ".active")
    if marker.exists():
        name = marker.read_text(encoding="utf-8").strip()
        return name if name else None
    return None


def set_active_profile(base: str, profile: str) -> None:
    """Write the active profile name to '<base>.active'."""
    Path(base + ".active").write_text(profile + "\n", encoding="utf-8")
