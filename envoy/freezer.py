"""freezer.py — Freeze and thaw env snapshots as immutable read-only exports."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Optional

FREEZE_HEADER = "# envoy:frozen"


class FreezeError(Exception):
    pass


def freeze_env(
    env: Dict[str, str],
    *,
    note: str = "",
    keys: Optional[List[str]] = None,
) -> str:
    """Serialize env to a frozen JSON blob with metadata."""
    if keys is not None:
        missing = [k for k in keys if k not in env]
        if missing:
            raise FreezeError(f"Keys not found in env: {', '.join(missing)}")
        env = {k: env[k] for k in keys}

    payload = {
        "version": 1,
        "frozen_at": int(time.time()),
        "note": note,
        "env": env,
    }
    return FREEZE_HEADER + "\n" + json.dumps(payload, indent=2)


def thaw_env(content: str) -> Dict[str, str]:
    """Parse a frozen blob back into an env dict."""
    lines = content.strip().splitlines()
    if not lines or lines[0].strip() != FREEZE_HEADER:
        raise FreezeError("Content does not appear to be a frozen env file.")
    body = "\n".join(lines[1:])
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise FreezeError(f"Malformed frozen env: {exc}") from exc
    if "env" not in payload:
        raise FreezeError("Frozen payload missing 'env' key.")
    return dict(payload["env"])


def is_frozen(content: str) -> bool:
    """Return True if content looks like a frozen env file."""
    return content.strip().startswith(FREEZE_HEADER)


def freeze_metadata(content: str) -> Dict:
    """Return the metadata portion of a frozen env (excludes env values)."""
    lines = content.strip().splitlines()
    if not lines or lines[0].strip() != FREEZE_HEADER:
        raise FreezeError("Content does not appear to be a frozen env file.")
    body = "\n".join(lines[1:])
    payload = json.loads(body)
    return {
        "version": payload.get("version"),
        "frozen_at": payload.get("frozen_at"),
        "note": payload.get("note", ""),
        "key_count": len(payload.get("env", {})),
    }
