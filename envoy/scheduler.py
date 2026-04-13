"""Schedule recurring sync or backup tasks using cron-style expressions."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional

_SCHEDULE_FILE = Path(".envoy_schedules.json")

VALID_ACTIONS = {"pull", "push", "backup", "rotate"}
_CRON_RE = re.compile(
    r"^(\*|\d+)\s+(\*|\d+)\s+(\*|\d+)\s+(\*|\d+)\s+(\*|\d+)$"
)


class SchedulerError(Exception):
    pass


@dataclass
class ScheduledTask:
    name: str
    action: str
    cron: str
    env_file: str
    args: dict = field(default_factory=dict)
    enabled: bool = True

    def __repr__(self) -> str:
        status = "on" if self.enabled else "off"
        return f"<ScheduledTask {self.name!r} action={self.action!r} cron={self.cron!r} [{status}]>"


def _schedule_path(base: Optional[Path] = None) -> Path:
    return (base or Path.cwd()) / ".envoy_schedules.json"


def load_schedules(base: Optional[Path] = None) -> List[ScheduledTask]:
    path = _schedule_path(base)
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    return [ScheduledTask(**item) for item in data]


def save_schedules(tasks: List[ScheduledTask], base: Optional[Path] = None) -> None:
    path = _schedule_path(base)
    path.write_text(json.dumps([asdict(t) for t in tasks], indent=2))


def add_task(tasks: List[ScheduledTask], task: ScheduledTask) -> List[ScheduledTask]:
    if any(t.name == task.name for t in tasks):
        raise SchedulerError(f"Task {task.name!r} already exists.")
    if task.action not in VALID_ACTIONS:
        raise SchedulerError(f"Unknown action {task.action!r}. Choose from: {sorted(VALID_ACTIONS)}")
    if not _CRON_RE.match(task.cron):
        raise SchedulerError(f"Invalid cron expression: {task.cron!r}")
    return tasks + [task]


def remove_task(tasks: List[ScheduledTask], name: str) -> List[ScheduledTask]:
    remaining = [t for t in tasks if t.name != name]
    if len(remaining) == len(tasks):
        raise SchedulerError(f"Task {name!r} not found.")
    return remaining


def toggle_task(tasks: List[ScheduledTask], name: str, enabled: bool) -> List[ScheduledTask]:
    updated = []
    found = False
    for t in tasks:
        if t.name == name:
            updated.append(ScheduledTask(**{**asdict(t), "enabled": enabled}))
            found = True
        else:
            updated.append(t)
    if not found:
        raise SchedulerError(f"Task {name!r} not found.")
    return updated


def get_task(tasks: List[ScheduledTask], name: str) -> ScheduledTask:
    for t in tasks:
        if t.name == name:
            return t
    raise SchedulerError(f"Task {name!r} not found.")
