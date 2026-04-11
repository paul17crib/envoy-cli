"""Merge multiple env dicts with configurable conflict resolution strategies."""

from typing import Dict, List, Literal, Optional

EnvDict = Dict[str, str]
Strategy = Literal["first", "last", "error"]


class MergeConflictError(Exception):
    """Raised when a key conflict is detected and strategy is 'error'."""

    def __init__(self, key: str, values: List[str]) -> None:
        self.key = key
        self.values = values
        super().__init__(
            f"Merge conflict on key '{key}': found values {values}"
        )


def merge_all(
    envs: List[EnvDict],
    strategy: Strategy = "last",
    keys: Optional[List[str]] = None,
) -> EnvDict:
    """Merge a list of env dicts into one.

    Args:
        envs: Ordered list of env dicts to merge.
        strategy: How to handle key conflicts.
            'first'  – keep the first occurrence.
            'last'   – keep the last occurrence (default).
            'error'  – raise MergeConflictError on any conflict.
        keys: If provided, only include these keys in the result.

    Returns:
        Merged env dict.
    """
    if not envs:
        return {}

    result: EnvDict = {}
    seen: Dict[str, List[str]] = {}

    for env in envs:
        for k, v in env.items():
            if keys is not None and k not in keys:
                continue
            seen.setdefault(k, [])
            seen[k].append(v)

    for k, values in seen.items():
        if len(values) > 1 and strategy == "error":
            raise MergeConflictError(k, values)
        result[k] = values[0] if strategy == "first" else values[-1]

    return result


def find_conflicts(envs: List[EnvDict]) -> Dict[str, List[str]]:
    """Return a mapping of keys that appear with different values across envs."""
    seen: Dict[str, List[str]] = {}
    for env in envs:
        for k, v in env.items():
            seen.setdefault(k, [])
            if v not in seen[k]:
                seen[k].append(v)
    return {k: vs for k, vs in seen.items() if len(vs) > 1}


def keys_in_all(envs: List[EnvDict]) -> List[str]:
    """Return keys that are present in every env dict."""
    if not envs:
        return []
    common = set(envs[0].keys())
    for env in envs[1:]:
        common &= set(env.keys())
    return sorted(common)


def keys_in_any(envs: List[EnvDict]) -> List[str]:
    """Return all keys that appear in at least one env dict."""
    all_keys: set = set()
    for env in envs:
        all_keys |= set(env.keys())
    return sorted(all_keys)
