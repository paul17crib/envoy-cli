"""Trace which .env keys are actually used in source code files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Set


class TracerError(Exception):
    pass


TRACE_PATTERNS = [
    re.compile(r'os\.environ\.get\(["\']([A-Z0-9_]+)["\']'),
    re.compile(r'os\.environ\[["\']([A-Z0-9_]+)["\']\]'),
    re.compile(r'os\.getenv\(["\']([A-Z0-9_]+)["\']'),
    re.compile(r'process\.env\.([A-Z0-9_]+)'),
    re.compile(r'ENV\[["\']([A-Z0-9_]+)["\']\]'),
    re.compile(r'getenv\(["\']([A-Z0-9_]+)["\']'),
]


def scan_file(path: Path, patterns: List[re.Pattern] | None = None) -> Set[str]:
    """Return all env key references found in a single source file."""
    if patterns is None:
        patterns = TRACE_PATTERNS
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        raise TracerError(f"Cannot read {path}: {exc}") from exc
    found: Set[str] = set()
    for pattern in patterns:
        found.update(pattern.findall(text))
    return found


def scan_directory(
    directory: Path,
    extensions: List[str] | None = None,
    patterns: List[re.Pattern] | None = None,
) -> Dict[str, Set[str]]:
    """Scan all matching files under *directory*.

    Returns a mapping of ``filepath -> set_of_keys``.
    """
    if extensions is None:
        extensions = [".py", ".js", ".ts", ".rb", ".go", ".sh"]
    results: Dict[str, Set[str]] = {}
    for ext in extensions:
        for filepath in directory.rglob(f"*{ext}"):
            keys = scan_file(filepath, patterns)
            if keys:
                results[str(filepath)] = keys
    return results


def trace_env(
    env: Dict[str, str],
    directory: Path,
    extensions: List[str] | None = None,
) -> Dict[str, List[str]]:
    """For each env key, return list of files that reference it."""
    file_map = scan_directory(directory, extensions)
    usage: Dict[str, List[str]] = {key: [] for key in env}
    for filepath, keys in file_map.items():
        for key in keys:
            if key in usage:
                usage[key].append(filepath)
    return usage


def unused_keys(
    env: Dict[str, str],
    directory: Path,
    extensions: List[str] | None = None,
) -> List[str]:
    """Return keys defined in *env* that are not referenced in *directory*."""
    usage = trace_env(env, directory, extensions)
    return sorted(k for k, files in usage.items() if not files)


def undeclared_refs(
    env: Dict[str, str],
    directory: Path,
    extensions: List[str] | None = None,
) -> Dict[str, List[str]]:
    """Return references found in code that are NOT defined in *env*."""
    file_map = scan_directory(directory, extensions)
    all_refs: Dict[str, List[str]] = {}
    for filepath, keys in file_map.items():
        for key in keys:
            if key not in env:
                all_refs.setdefault(key, []).append(filepath)
    return all_refs
