"""Snapshot management for .env files — create, list, and restore named snapshots."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_SNAPSHOT_DIR = ".envoy_snapshots"


def snapshot_dir(base_dir: str = ".") -> Path:
    return Path(base_dir) / DEFAULT_SNAPSHOT_DIR


def _snapshot_path(name: str, base_dir: str = ".") -> Path:
    return snapshot_dir(base_dir) / f"{name}.json"


def save_snapshot(name: str, env: Dict[str, str], base_dir: str = ".", note: str = "") -> Path:
    """Persist a named snapshot of the given env dict."""
    sdir = snapshot_dir(base_dir)
    sdir.mkdir(parents=True, exist_ok=True)
    path = _snapshot_path(name, base_dir)
    payload = {
        "name": name,
        "note": note,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "env": env,
    }
    path.write_text(json.dumps(payload, indent=2))
    return path


def load_snapshot(name: str, base_dir: str = ".") -> Dict[str, str]:
    """Load a snapshot by name; raises FileNotFoundError if missing."""
    path = _snapshot_path(name, base_dir)
    if not path.exists():
        raise FileNotFoundError(f"Snapshot '{name}' not found.")
    payload = json.loads(path.read_text())
    return payload["env"]


def list_snapshots(base_dir: str = ".") -> List[dict]:
    """Return metadata for all saved snapshots, sorted by creation time."""
    sdir = snapshot_dir(base_dir)
    if not sdir.exists():
        return []
    results = []
    for f in sdir.glob("*.json"):
        try:
            payload = json.loads(f.read_text())
            results.append({
                "name": payload.get("name", f.stem),
                "note": payload.get("note", ""),
                "created_at": payload.get("created_at", ""),
                "key_count": len(payload.get("env", {})),
            })
        except (json.JSONDecodeError, KeyError):
            continue
    results.sort(key=lambda x: x["created_at"])
    return results


def delete_snapshot(name: str, base_dir: str = ".") -> bool:
    """Delete a snapshot by name. Returns True if deleted, False if not found."""
    path = _snapshot_path(name, base_dir)
    if not path.exists():
        return False
    path.unlink()
    return True
