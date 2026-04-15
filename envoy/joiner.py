"""joiner.py — Combine values from multiple env keys into a single new key."""

from __future__ import annotations

from typing import Dict, List, Optional


class JoinerError(Exception):
    """Raised when a join operation cannot be completed."""


def join_keys(
    env: Dict[str, str],
    keys: List[str],
    dest: str,
    separator: str = " ",
    missing_ok: bool = False,
    overwrite: bool = True,
) -> Dict[str, str]:
    """Concatenate values of *keys* with *separator* and store in *dest*.

    Args:
        env: Source environment mapping.
        keys: Ordered list of keys whose values will be joined.
        dest: Destination key name for the joined value.
        separator: String placed between each value segment.
        missing_ok: When True, absent keys are silently skipped.
                    When False, a JoinerError is raised.
        overwrite: When False, raise JoinerError if *dest* already exists.

    Returns:
        A new dict with the joined key added (original is not mutated).
    """
    if not keys:
        raise JoinerError("At least one source key must be provided.")
    if not dest:
        raise JoinerError("Destination key must not be empty.")
    if not overwrite and dest in env:
        raise JoinerError(f"Destination key '{dest}' already exists and overwrite=False.")

    segments: List[str] = []
    for key in keys:
        if key not in env:
            if missing_ok:
                continue
            raise JoinerError(f"Source key '{key}' not found in env.")
        segments.append(env[key])

    result = dict(env)
    result[dest] = separator.join(segments)
    return result


def split_key(
    env: Dict[str, str],
    source: str,
    dest_keys: List[str],
    separator: str = " ",
    overwrite: bool = True,
) -> Dict[str, str]:
    """Split the value of *source* by *separator* and distribute into *dest_keys*.

    If the number of segments differs from len(dest_keys), a JoinerError is raised.
    """
    if source not in env:
        raise JoinerError(f"Source key '{source}' not found in env.")
    if not dest_keys:
        raise JoinerError("At least one destination key must be provided.")

    segments = env[source].split(separator)
    if len(segments) != len(dest_keys):
        raise JoinerError(
            f"Expected {len(dest_keys)} segments after splitting '{source}' "
            f"by '{separator}', got {len(segments)}."
        )

    result = dict(env)
    for key, value in zip(dest_keys, segments):
        if not overwrite and key in result:
            raise JoinerError(f"Destination key '{key}' already exists and overwrite=False.")
        result[key] = value
    return result


def get_joined_keys(original: Dict[str, str], updated: Dict[str, str]) -> List[str]:
    """Return keys that are new or changed between *original* and *updated*."""
    return [
        k for k, v in updated.items()
        if k not in original or original[k] != v
    ]
