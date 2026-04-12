"""Summarize an env dict into human-readable statistics and insights."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envoy.masker import is_sensitive_key


@dataclass
class EnvSummary:
    total: int = 0
    sensitive_count: int = 0
    empty_count: int = 0
    prefixes: Dict[str, int] = field(default_factory=dict)
    longest_key: str = ""
    longest_value_key: str = ""

    @property
    def non_sensitive_count(self) -> int:
        return self.total - self.sensitive_count

    @property
    def filled_count(self) -> int:
        return self.total - self.empty_count


def _extract_prefix(key: str, delimiter: str = "_") -> str:
    """Return the first segment of a key before the delimiter."""
    parts = key.split(delimiter, 1)
    return parts[0] if len(parts) > 1 else ""


def summarize(env: Dict[str, str], delimiter: str = "_") -> EnvSummary:
    """Build an EnvSummary from an env mapping."""
    summary = EnvSummary()
    summary.total = len(env)

    max_key_len = -1
    max_val_len = -1

    for key, value in env.items():
        if is_sensitive_key(key):
            summary.sensitive_count += 1
        if value == "":
            summary.empty_count += 1

        prefix = _extract_prefix(key, delimiter)
        if prefix:
            summary.prefixes[prefix] = summary.prefixes.get(prefix, 0) + 1

        if len(key) > max_key_len:
            max_key_len = len(key)
            summary.longest_key = key

        if len(value) > max_val_len:
            max_val_len = len(value)
            summary.longest_value_key = key

    return summary


def format_summary(summary: EnvSummary) -> List[str]:
    """Return a list of human-readable lines describing the summary."""
    lines = [
        f"Total keys      : {summary.total}",
        f"Sensitive keys  : {summary.sensitive_count}",
        f"Non-sensitive   : {summary.non_sensitive_count}",
        f"Filled values   : {summary.filled_count}",
        f"Empty values    : {summary.empty_count}",
    ]
    if summary.longest_key:
        lines.append(f"Longest key     : {summary.longest_key}")
    if summary.longest_value_key:
        lines.append(f"Longest value @ : {summary.longest_value_key}")
    if summary.prefixes:
        top = sorted(summary.prefixes.items(), key=lambda x: -x[1])[:5]
        top_str = ", ".join(f"{p}({c})" for p, c in top)
        lines.append(f"Top prefixes    : {top_str}")
    return lines
