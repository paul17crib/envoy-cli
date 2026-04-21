"""Compose a new env dict by applying a sequence of named transforms to an existing env."""
from __future__ import annotations

from typing import Callable, Dict, List, Optional

Env = Dict[str, str]
Step = Callable[[Env], Env]


class ComposerError(Exception):
    """Raised when a composition step fails."""


_REGISTRY: Dict[str, Step] = {}


def register(name: str, fn: Step) -> None:
    """Register a named composition step."""
    _REGISTRY[name] = fn


def list_steps() -> List[str]:
    """Return names of all registered steps."""
    return sorted(_REGISTRY.keys())


def get_step(name: str) -> Step:
    """Return a registered step by name, raising ComposerError if unknown."""
    if name not in _REGISTRY:
        raise ComposerError(f"Unknown composition step: {name!r}. Available: {list_steps()}")
    return _REGISTRY[name]


def compose(env: Env, steps: List[str]) -> Env:
    """Apply a sequence of named steps to *env*, returning the final env.

    Each step receives the output of the previous step.  The original env
    is never mutated.
    """
    result: Env = dict(env)
    for name in steps:
        fn = get_step(name)
        result = fn(result)
    return result


def compose_with_fns(env: Env, steps: List[Step]) -> Env:
    """Apply a sequence of callable steps to *env*."""
    result: Env = dict(env)
    for fn in steps:
        result = fn(result)
    return result


def preview_compose(env: Env, steps: List[str]) -> List[Dict[str, object]]:
    """Return a list of snapshots showing env state after each step."""
    snapshots: List[Dict[str, object]] = []
    current: Env = dict(env)
    for name in steps:
        fn = get_step(name)
        current = fn(current)
        snapshots.append({"step": name, "keys": len(current), "env": dict(current)})
    return snapshots


# ---------------------------------------------------------------------------
# Built-in steps
# ---------------------------------------------------------------------------

def _strip_empty(env: Env) -> Env:
    return {k: v for k, v in env.items() if v}


def _upper_keys(env: Env) -> Env:
    return {k.upper(): v for k, v in env.items()}


def _lower_values(env: Env) -> Env:
    return {k: v.lower() for k, v in env.items()}


def _strip_whitespace(env: Env) -> Env:
    return {k: v.strip() for k, v in env.items()}


register("strip_empty", _strip_empty)
register("upper_keys", _upper_keys)
register("lower_values", _lower_values)
register("strip_whitespace", _strip_whitespace)
