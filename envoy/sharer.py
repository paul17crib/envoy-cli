"""envoy.sharer — Generate shareable, time-limited env snapshots with optional secret redaction."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Dict, Optional

from envoy.masker import mask_env
from envoy.parser import serialize_env

SHARE_DIR_NAME = ".envoy_shares"


class ShareError(Exception):
    pass


def _share_dir(base: Path) -> Path:
    d = base / SHARE_DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def _token(label: str) -> str:
    raw = f"{label}-{time.time()}"
    return hashlib.sha1(raw.encode()).hexdigest()[:12]


def create_share(
    env: Dict[str, str],
    label: str,
    ttl_seconds: int = 3600,
    mask: bool = True,
    base: Optional[Path] = None,
) -> str:
    """Persist a shareable snapshot and return its token."""
    if not label:
        raise ShareError("label must not be empty")
    if ttl_seconds <= 0:
        raise ShareError("ttl_seconds must be positive")

    shared_env = mask_env(env) if mask else dict(env)
    token = _token(label)
    record = {
        "label": label,
        "token": token,
        "created_at": time.time(),
        "expires_at": time.time() + ttl_seconds,
        "masked": mask,
        "env": shared_env,
    }
    target = _share_dir(base or Path(".")) / f"{token}.json"
    target.write_text(json.dumps(record, indent=2))
    return token


def load_share(token: str, base: Optional[Path] = None) -> Dict[str, str]:
    """Load a share by token, raising ShareError if missing or expired."""
    path = _share_dir(base or Path(".")) / f"{token}.json"
    if not path.exists():
        raise ShareError(f"share not found: {token}")
    record = json.loads(path.read_text())
    if time.time() > record["expires_at"]:
        raise ShareError(f"share expired: {token}")
    return record["env"]


def list_shares(base: Optional[Path] = None) -> list:
    """Return metadata for all shares (expired or not)."""
    results = []
    for p in _share_dir(base or Path(".")).glob("*.json"):
        try:
            record = json.loads(p.read_text())
            record["expired"] = time.time() > record["expires_at"]
            results.append(record)
        except Exception:
            continue
    return sorted(results, key=lambda r: r.get("created_at", 0))


def revoke_share(token: str, base: Optional[Path] = None) -> bool:
    """Delete a share file. Returns True if removed, False if not found."""
    path = _share_dir(base or Path(".")) / f"{token}.json"
    if path.exists():
        path.unlink()
        return True
    return False
