"""Highlight specific keys or values in an env mapping for display purposes."""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

ANSI_YELLOW = "\033[33m"
ANSI_CYAN = "\033[36m"
ANSI_RESET = "\033[0m"


def highlight_text(text: str, pattern: str, color: str = ANSI_YELLOW, case_sensitive: bool = False) -> str:
    """Wrap all occurrences of pattern in text with ANSI color codes."""
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        compiled = re.compile(re.escape(pattern), flags)
    except re.error:
        return text
    return compiled.sub(lambda m: f"{color}{m.group()}{ANSI_RESET}", text)


def highlight_env(
    env: Dict[str, str],
    pattern: str,
    search_keys: bool = True,
    search_values: bool = True,
    case_sensitive: bool = False,
    color: str = ANSI_YELLOW,
) -> List[Tuple[str, str, bool]]:
    """Return a list of (key, value, matched) tuples with highlights applied.

    Only entries where the pattern matches in the key or value are included
    (matched=True). Non-matching entries are included with matched=False so
    callers can choose whether to display them.
    """
    results: List[Tuple[str, str, bool]] = []
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        compiled = re.compile(re.escape(pattern), flags)
    except re.error:
        return [(k, v, False) for k, v in env.items()]

    for key, value in env.items():
        key_match = bool(compiled.search(key)) if search_keys else False
        val_match = bool(compiled.search(value)) if search_values else False
        matched = key_match or val_match

        highlighted_key = highlight_text(key, pattern, color, case_sensitive) if key_match else key
        highlighted_val = highlight_text(value, pattern, color, case_sensitive) if val_match else value
        results.append((highlighted_key, highlighted_val, matched))

    return results


def filter_highlighted(
    entries: List[Tuple[str, str, bool]],
    only_matches: bool = True,
) -> List[Tuple[str, str]]:
    """Filter highlight results to only matched (or all) entries."""
    if only_matches:
        return [(k, v) for k, v, matched in entries if matched]
    return [(k, v) for k, v, _ in entries]


def count_matches(entries: List[Tuple[str, str, bool]]) -> int:
    """Return the number of matched entries."""
    return sum(1 for _, _, matched in entries if matched)
