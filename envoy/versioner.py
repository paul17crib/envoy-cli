"""versioner.py — track and manage versioned snapshots of env files."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional

VERSION_DIR = ".envoy_versions"


class VersionError(Exception):
    pass


def _version_dir(base_dir: Path) -> Path:
    return base_dir / VERSION_DIR


def _env_hash(env: Dict[str, str]) -> str:
    canonical = json.dumps(env, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(canonical.encode()).hexdigest()[:10]


def save_version(env: Dict[str, str], label: str, base_dir: Path) -> Path:
    """Save a versioned copy of env under a label. Raises VersionError on collision."""
    vdir = _version_dir(base_dir)
    vdir.mkdir(parents=True, exist_ok=True)
    vfile = vdir / f"{label}.json"
    if vfile.exists():
        raise VersionError(f"Version '{label}' already exists. Use a different label.")
    payload = {"label": label, "hash": _env_hash(env), "env": env}
    vfile.write_text(json.dumps(payload, indent=2))
    return vfile


def load_version(label: str, base_dir: Path) -> Dict[str, str]:
    """Load a versioned env by label. Raises VersionError if not found."""
    vfile = _version_dir(base_dir) / f"{label}.json"
    if not vfile.exists():
        raise VersionError(f"Version '{label}' not found.")
    payload = json.loads(vfile.read_text())
    return payload["env"]


def list_versions(base_dir: Path) -> List[str]:
    """Return sorted list of saved version labels."""
    vdir = _version_dir(base_dir)
    if not vdir.exists():
        return []
    return sorted(p.stem for p in vdir.glob("*.json"))


def delete_version(label: str, base_dir: Path) -> None:
    """Delete a saved version. Raises VersionError if not found."""
    vfile = _version_dir(base_dir) / f"{label}.json"
    if not vfile.exists():
        raise VersionError(f"Version '{label}' not found.")
    vfile.unlink()


def diff_version(
    env: Dict[str, str], label: str, base_dir: Path
) -> Dict[str, Optional[str]]:
    """Return keys that differ between current env and saved version.

    Returns a dict of {key: saved_value_or_None} for keys that changed or
    are missing in the saved version.
    """
    saved = load_version(label, base_dir)
    changes: Dict[str, Optional[str]] = {}
    all_keys = set(env) | set(saved)
    for key in all_keys:
        if env.get(key) != saved.get(key):
            changes[key] = saved.get(key)
    return changes
