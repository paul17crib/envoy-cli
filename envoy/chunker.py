"""chunker.py — Split an env dict into fixed-size chunks."""

from __future__ import annotations

from typing import Dict, List


class ChunkerError(Exception):
    """Raised when chunking parameters are invalid."""


def chunk_env(
    env: Dict[str, str],
    size: int,
    *,
    keys: List[str] | None = None,
) -> List[Dict[str, str]]:
    """Split *env* into chunks of at most *size* key-value pairs.

    Args:
        env:  Source environment mapping.
        size: Maximum number of entries per chunk.  Must be >= 1.
        keys: Optional explicit key ordering.  Unknown keys are ignored;
              keys absent from *env* are silently skipped.

    Returns:
        A list of dicts, each containing at most *size* entries.
        Returns ``[{}]`` when *env* is empty.
    """
    if size < 1:
        raise ChunkerError(f"chunk size must be >= 1, got {size}")

    if keys is not None:
        ordered = [(k, env[k]) for k in keys if k in env]
    else:
        ordered = list(env.items())

    if not ordered:
        return [{}]

    return [
        dict(ordered[i : i + size])
        for i in range(0, len(ordered), size)
    ]


def chunk_count(env: Dict[str, str], size: int) -> int:
    """Return the number of chunks that *chunk_env* would produce."""
    if size < 1:
        raise ChunkerError(f"chunk size must be >= 1, got {size}")
    if not env:
        return 1
    total = len(env)
    return (total + size - 1) // size


def merge_chunks(chunks: List[Dict[str, str]]) -> Dict[str, str]:
    """Merge a list of chunk dicts back into a single env mapping.

    Later chunks win on duplicate keys.
    """
    result: Dict[str, str] = {}
    for chunk in chunks:
        result.update(chunk)
    return result
