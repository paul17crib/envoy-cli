"""Pin specific keys to a snapshot, allowing drift detection against current env."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

PIN_FILE_DEFAULT = ".env.pins"


class PinError(Exception):
    pass


def load_pins(pin_file: str = PIN_FILE_DEFAULT) -> Dict[str, str]:
    """Load pinned key-value pairs from a JSON pin file."""
    path = Path(pin_file)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PinError(f"Corrupt pin file '{pin_file}': {exc}") from exc


def save_pins(pins: Dict[str, str], pin_file: str = PIN_FILE_DEFAULT) -> None:
    """Persist pinned key-value pairs to a JSON pin file."""
    Path(pin_file).write_text(
        json.dumps(pins, indent=2, sort_keys=True), encoding="utf-8"
    )


def pin_keys(
    env: Dict[str, str],
    keys: List[str],
    existing_pins: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """Return an updated pins dict with the given keys pinned to their current values."""
    pins = dict(existing_pins) if existing_pins else {}
    for key in keys:
        if key not in env:
            raise PinError(f"Key '{key}' not found in environment.")
        pins[key] = env[key]
    return pins


def unpin_keys(
    keys: List[str], existing_pins: Dict[str, str]
) -> Dict[str, str]:
    """Return a pins dict with the specified keys removed."""
    pins = dict(existing_pins)
    for key in keys:
        if key not in pins:
            raise PinError(f"Key '{key}' is not currently pinned.")
        del pins[key]
    return pins


def check_drift(
    env: Dict[str, str], pins: Dict[str, str]
) -> Dict[str, dict]:
    """Compare current env against pinned values.

    Returns a mapping of drifted keys to {"pinned": ..., "current": ...}.
    """
    drift: Dict[str, dict] = {}
    for key, pinned_value in pins.items():
        current = env.get(key)
        if current is None:
            drift[key] = {"pinned": pinned_value, "current": None, "status": "missing"}
        elif current != pinned_value:
            drift[key] = {"pinned": pinned_value, "current": current, "status": "changed"}
    return drift
