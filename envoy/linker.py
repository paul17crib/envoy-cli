"""linker.py — Link (alias) keys across two env dicts using a mapping file."""

from __future__ import annotations

from typing import Dict, List, Tuple


class LinkerError(Exception):
    """Raised when a link operation cannot be completed."""


LinkMap = Dict[str, str]  # source_key -> dest_key


def build_link_map(pairs: List[Tuple[str, str]]) -> LinkMap:
    """Build a link map from a list of (source, dest) tuples.

    Raises LinkerError on duplicate source keys.
    """
    mapping: LinkMap = {}
    for src, dst in pairs:
        if src in mapping:
            raise LinkerError(f"Duplicate source key in link map: {src!r}")
        mapping[src] = dst
    return mapping


def apply_links(
    env: Dict[str, str],
    link_map: LinkMap,
    overwrite: bool = False,
) -> Dict[str, str]:
    """Return a new env dict with linked keys added.

    For each (src -> dst) in *link_map*, the value of *src* is copied to *dst*.
    If *overwrite* is False and *dst* already exists, the key is skipped.
    Raises LinkerError if *src* is not present in *env*.
    """
    result = dict(env)
    for src, dst in link_map.items():
        if src not in env:
            raise LinkerError(f"Source key not found in env: {src!r}")
        if dst in result and not overwrite:
            continue
        result[dst] = env[src]
    return result


def get_linked_keys(
    env: Dict[str, str],
    link_map: LinkMap,
) -> List[str]:
    """Return the list of destination keys that would be written by apply_links."""
    return [dst for src, dst in link_map.items() if src in env]


def parse_link_file(text: str) -> LinkMap:
    """Parse a simple link-map file.

    Each non-blank, non-comment line must have the form::

        SOURCE_KEY -> DEST_KEY

    Raises LinkerError on malformed lines.
    """
    mapping: LinkMap = {}
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "->" not in line:
            raise LinkerError(f"Line {lineno}: expected 'SRC -> DST', got {raw!r}")
        src, _, dst = line.partition("->")
        src, dst = src.strip(), dst.strip()
        if not src or not dst:
            raise LinkerError(f"Line {lineno}: empty key in {raw!r}")
        if src in mapping:
            raise LinkerError(f"Line {lineno}: duplicate source key {src!r}")
        mapping[src] = dst
    return mapping
