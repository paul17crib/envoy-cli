"""envoy.mapper — Build key-to-file mappings across multiple .env files."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, NamedTuple

from envoy.parser import parse_env_file


class MapEntry(NamedTuple):
    key: str
    value: str
    source: str  # file path as string


class MapperError(Exception):
    pass


def build_key_map(paths: List[str]) -> Dict[str, List[MapEntry]]:
    """Return a mapping of key -> list of MapEntry across all given files.

    Keys appearing in multiple files will have multiple entries.
    """
    result: Dict[str, List[MapEntry]] = {}
    for path in paths:
        p = Path(path)
        if not p.exists():
            raise MapperError(f"File not found: {path}")
        env = parse_env_file(path)
        for key, value in env.items():
            result.setdefault(key, []).append(MapEntry(key=key, value=value, source=path))
    return result


def find_duplicates(key_map: Dict[str, List[MapEntry]]) -> Dict[str, List[MapEntry]]:
    """Return only keys that appear in more than one file."""
    return {k: v for k, v in key_map.items() if len(v) > 1}


def find_unique(key_map: Dict[str, List[MapEntry]]) -> Dict[str, List[MapEntry]]:
    """Return only keys that appear in exactly one file."""
    return {k: v for k, v in key_map.items() if len(v) == 1}


def keys_in_all(key_map: Dict[str, List[MapEntry]], total_files: int) -> List[str]:
    """Return keys that appear in every file."""
    return [k for k, entries in key_map.items() if len(entries) == total_files]


def format_map_report(key_map: Dict[str, List[MapEntry]], show_values: bool = False) -> str:
    """Return a human-readable report of the key map."""
    lines: List[str] = []
    for key in sorted(key_map):
        entries = key_map[key]
        lines.append(f"{key} ({len(entries)} file(s)):")
        for entry in entries:
            if show_values:
                lines.append(f"  {entry.source} = {entry.value}")
            else:
                lines.append(f"  {entry.source}")
    return "\n".join(lines)
