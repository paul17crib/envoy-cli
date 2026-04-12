"""Split an env dict into multiple files based on a key prefix or pattern."""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple


class SplitError(Exception):
    """Raised when a split operation cannot be completed."""


def split_by_prefix(
    env: Dict[str, str],
    delimiter: str = "_",
    strip_prefix: bool = False,
) -> Dict[str, Dict[str, str]]:
    """Group keys by their first prefix segment.

    Keys with no delimiter go into the '__ungrouped__' bucket.
    """
    groups: Dict[str, Dict[str, str]] = {}
    for key, value in env.items():
        if delimiter in key:
            prefix, rest = key.split(delimiter, 1)
            bucket = prefix.upper()
            mapped_key = rest if strip_prefix else key
        else:
            bucket = "__ungrouped__"
            mapped_key = key
        groups.setdefault(bucket, {})[mapped_key] = value
    return groups


def split_by_pattern(
    env: Dict[str, str],
    patterns: Dict[str, str],
    default_bucket: str = "__other__",
) -> Dict[str, Dict[str, str]]:
    """Assign each key to the first matching named pattern bucket.

    ``patterns`` maps bucket name -> regex pattern string.
    Unmatched keys fall into ``default_bucket``.
    """
    compiled: List[Tuple[str, re.Pattern[str]]] = [
        (name, re.compile(pat, re.IGNORECASE)) for name, pat in patterns.items()
    ]
    groups: Dict[str, Dict[str, str]] = {}
    for key, value in env.items():
        assigned = False
        for bucket, regex in compiled:
            if regex.search(key):
                groups.setdefault(bucket, {})[key] = value
                assigned = True
                break
        if not assigned:
            groups.setdefault(default_bucket, {})[key] = value
    return groups


def list_split_keys(
    groups: Dict[str, Dict[str, str]],
) -> Dict[str, List[str]]:
    """Return a mapping of bucket name -> sorted list of keys."""
    return {bucket: sorted(keys.keys()) for bucket, keys in groups.items()}


def get_split_bucket(
    groups: Dict[str, Dict[str, str]],
    bucket: str,
) -> Optional[Dict[str, str]]:
    """Retrieve a single bucket by name, or None if it does not exist."""
    return groups.get(bucket)
