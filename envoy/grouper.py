"""Group env variables by prefix, suffix, or custom pattern."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Dict, List, Optional


def group_by_prefix(env: dict, delimiter: str = "_") -> Dict[str, dict]:
    """Group env keys by their first segment before the delimiter."""
    groups: Dict[str, dict] = defaultdict(dict)
    for key, value in env.items():
        if delimiter in key:
            prefix = key.split(delimiter, 1)[0]
        else:
            prefix = "__ungrouped__"
        groups[prefix][key] = value
    return dict(groups)


def group_by_suffix(env: dict, delimiter: str = "_") -> Dict[str, dict]:
    """Group env keys by their last segment after the delimiter."""
    groups: Dict[str, dict] = defaultdict(dict)
    for key, value in env.items():
        if delimiter in key:
            suffix = key.rsplit(delimiter, 1)[-1]
        else:
            suffix = "__ungrouped__"
        groups[suffix][key] = value
    return dict(groups)


def group_by_pattern(env: dict, patterns: List[str]) -> Dict[str, dict]:
    """Group env keys by the first matching regex pattern label.

    Each entry in `patterns` is a string like "label:regex".
    Keys that match no pattern are placed under "__other__".
    """
    compiled: List[tuple] = []
    for entry in patterns:
        if ":" not in entry:
            raise ValueError(f"Pattern entry must be 'label:regex', got: {entry!r}")
        label, regex = entry.split(":", 1)
        compiled.append((label.strip(), re.compile(regex.strip())))

    groups: Dict[str, dict] = defaultdict(dict)
    for key, value in env.items():
        matched = False
        for label, pattern in compiled:
            if pattern.search(key):
                groups[label][key] = value
                matched = True
                break
        if not matched:
            groups["__other__"][key] = value
    return dict(groups)


def list_groups(groups: Dict[str, dict]) -> List[str]:
    """Return sorted group names."""
    return sorted(groups.keys())


def get_group(groups: Dict[str, dict], name: str) -> Optional[dict]:
    """Return a specific group by name, or None if not found."""
    return groups.get(name)
