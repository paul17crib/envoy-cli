"""Walk and collect .env files from a directory tree."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator, List, Optional


class WalkerError(Exception):
    """Raised when directory walking fails."""


def _is_env_file(path: Path, patterns: List[str]) -> bool:
    """Return True if path matches any of the given filename patterns."""
    name = path.name
    return any(
        name == p or name.endswith(p) if p.startswith(".") else name == p
        for p in patterns
    )


def walk_env_files(
    root: str | Path,
    patterns: Optional[List[str]] = None,
    max_depth: int = 10,
    skip_hidden: bool = True,
) -> Iterator[Path]:
    """Yield .env file paths found under *root* up to *max_depth* levels deep.

    Args:
        root: Directory to start walking from.
        patterns: Filename patterns to match (default: common .env names).
        max_depth: Maximum directory depth to recurse into.
        skip_hidden: If True, skip directories starting with a dot.
    """
    if patterns is None:
        patterns = [".env", ".env.local", ".env.example", ".env.sample"]

    root = Path(root)
    if not root.is_dir():
        raise WalkerError(f"Not a directory: {root}")

    def _recurse(directory: Path, depth: int) -> Iterator[Path]:
        if depth > max_depth:
            return
        try:
            entries = sorted(directory.iterdir())
        except PermissionError:
            return
        for entry in entries:
            if skip_hidden and entry.name.startswith(".") and entry.is_dir():
                continue
            if entry.is_dir():
                yield from _recurse(entry, depth + 1)
            elif entry.is_file() and _is_env_file(entry, patterns):
                yield entry

    yield from _recurse(root, 0)


def collect_env_files(
    root: str | Path,
    patterns: Optional[List[str]] = None,
    max_depth: int = 10,
    skip_hidden: bool = True,
) -> List[Path]:
    """Return a sorted list of .env file paths found under *root*."""
    return list(
        walk_env_files(
            root,
            patterns=patterns,
            max_depth=max_depth,
            skip_hidden=skip_hidden,
        )
    )


def summarize_walk(root: str | Path, **kwargs) -> dict:
    """Return a summary dict with counts and paths for a directory walk."""
    files = collect_env_files(root, **kwargs)
    dirs = {str(f.parent) for f in files}
    return {
        "root": str(root),
        "total_files": len(files),
        "total_dirs": len(dirs),
        "files": [str(f) for f in files],
    }
