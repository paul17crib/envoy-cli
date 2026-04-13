"""planner.py — Build and describe a migration plan for .env key changes."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PlanStep:
    action: str          # 'add', 'remove', 'rename', 'update'
    key: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    new_key: Optional[str] = None

    def __repr__(self) -> str:
        if self.action == "rename":
            return f"[rename] {self.key} -> {self.new_key}"
        if self.action == "add":
            return f"[add]    {self.key}={self.new_value}"
        if self.action == "remove":
            return f"[remove] {self.key}"
        if self.action == "update":
            return f"[update] {self.key}: {self.old_value!r} -> {self.new_value!r}"
        return f"[{self.action}] {self.key}"


@dataclass
class MigrationPlan:
    steps: List[PlanStep] = field(default_factory=list)

    def add_step(self, step: PlanStep) -> None:
        self.steps.append(step)

    @property
    def is_empty(self) -> bool:
        return len(self.steps) == 0

    def by_action(self, action: str) -> List[PlanStep]:
        return [s for s in self.steps if s.action == action]


def build_plan(
    source: Dict[str, str],
    target: Dict[str, str],
    renames: Optional[Dict[str, str]] = None,
) -> MigrationPlan:
    """Compute a MigrationPlan that transforms *source* into *target*.

    Args:
        source: current env dict.
        target: desired env dict.
        renames: optional mapping of old_key -> new_key to treat as renames
                 rather than remove+add pairs.
    """
    plan = MigrationPlan()
    renames = renames or {}
    renamed_old = set(renames.keys())
    renamed_new = set(renames.values())

    # Renames first
    for old_key, new_key in renames.items():
        if old_key in source:
            plan.add_step(PlanStep(action="rename", key=old_key, new_key=new_key,
                                   old_value=source[old_key]))

    # Removals (keys in source not in target and not being renamed)
    for key in source:
        if key not in target and key not in renamed_old:
            plan.add_step(PlanStep(action="remove", key=key, old_value=source[key]))

    # Additions (keys in target not in source and not a rename destination)
    for key in target:
        if key not in source and key not in renamed_new:
            plan.add_step(PlanStep(action="add", key=key, new_value=target[key]))

    # Updates (keys present in both with different values)
    for key in source:
        if key in target and source[key] != target[key]:
            plan.add_step(PlanStep(action="update", key=key,
                                   old_value=source[key], new_value=target[key]))

    return plan


def apply_plan(env: Dict[str, str], plan: MigrationPlan) -> Dict[str, str]:
    """Apply *plan* to *env* and return the resulting dict (does not mutate)."""
    result = dict(env)
    for step in plan.steps:
        if step.action == "add":
            result[step.key] = step.new_value or ""
        elif step.action == "remove":
            result.pop(step.key, None)
        elif step.action == "update":
            result[step.key] = step.new_value or ""
        elif step.action == "rename" and step.new_key:
            value = result.pop(step.key, step.old_value or "")
            result[step.new_key] = value
    return result
