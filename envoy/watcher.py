"""Watch .env files for changes and report diffs."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional

from envoy.parser import parse_env_file
from envoy.differ import diff_envs, DiffEntry


@dataclass
class WatchEvent:
    path: str
    previous: Dict[str, str]
    current: Dict[str, str]
    changes: list = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def has_changes(self) -> bool:
        return len(self.changes) > 0


def _read_mtime(path: str) -> Optional[float]:
    try:
        return os.path.getmtime(path)
    except FileNotFoundError:
        return None


def _read_env(path: str) -> Dict[str, str]:
    try:
        return parse_env_file(path)
    except Exception:
        return {}


def watch_once(path: str, previous: Dict[str, str]) -> WatchEvent:
    """Read the file and return a WatchEvent comparing to previous state."""
    current = _read_env(path)
    changes = diff_envs(previous, current)
    return WatchEvent(
        path=path,
        previous=previous,
        current=current,
        changes=[c for c in changes if c.symbol != "="],
    )


def watch(
    path: str,
    callback: Callable[[WatchEvent], None],
    interval: float = 1.0,
    max_iterations: Optional[int] = None,
) -> None:
    """Poll a file for changes and invoke callback on each change."""
    previous = _read_env(path)
    last_mtime = _read_mtime(path)
    iterations = 0

    while max_iterations is None or iterations < max_iterations:
        time.sleep(interval)
        current_mtime = _read_mtime(path)
        if current_mtime != last_mtime:
            event = watch_once(path, previous)
            if event.has_changes():
                callback(event)
            previous = event.current
            last_mtime = current_mtime
        iterations += 1
