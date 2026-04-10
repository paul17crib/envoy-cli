"""Core cloning logic for duplicating and filtering .env data."""
from typing import Dict, Optional, List


def filter_keys(
    env: Dict[str, str],
    include: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
) -> Dict[str, str]:
    """Return a filtered copy of env.

    If *include* is given, only those keys are kept.
    If *exclude* is given, those keys are removed.
    Both can be combined: include is applied first, then exclude.
    """
    result = dict(env)

    if include is not None:
        result = {k: v for k, v in result.items() if k in include}

    if exclude is not None:
        result = {k: v for k, v in result.items() if k not in exclude}

    return result


def clone_env(
    env: Dict[str, str],
    include: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
) -> Dict[str, str]:
    """Return a filtered clone of *env* without mutating the original."""
    return filter_keys(env, include=include, exclude=exclude)


def missing_keys(env: Dict[str, str], keys: List[str]) -> List[str]:
    """Return keys from *keys* that are absent in *env*."""
    return [k for k in keys if k not in env]
