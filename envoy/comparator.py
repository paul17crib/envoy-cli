"""Compare two env dicts and produce a structured similarity report."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class ComparisonReport:
    shared_keys: List[str] = field(default_factory=list)
    only_in_left: List[str] = field(default_factory=list)
    only_in_right: List[str] = field(default_factory=list)
    differing_keys: List[str] = field(default_factory=list)
    matching_keys: List[str] = field(default_factory=list)

    @property
    def total_unique_keys(self) -> int:
        return len(set(self.shared_keys) | set(self.only_in_left) | set(self.only_in_right))

    @property
    def similarity_score(self) -> float:
        """Return a 0.0–1.0 score based on matching vs total unique keys."""
        total = self.total_unique_keys
        if total == 0:
            return 1.0
        return round(len(self.matching_keys) / total, 4)


def compare_envs(
    left: Dict[str, str],
    right: Dict[str, str],
) -> ComparisonReport:
    """Compare two env dicts and return a ComparisonReport."""
    left_keys = set(left)
    right_keys = set(right)
    shared = left_keys & right_keys

    only_left = sorted(left_keys - right_keys)
    only_right = sorted(right_keys - left_keys)
    shared_sorted = sorted(shared)

    matching = [k for k in shared_sorted if left[k] == right[k]]
    differing = [k for k in shared_sorted if left[k] != right[k]]

    return ComparisonReport(
        shared_keys=shared_sorted,
        only_in_left=only_left,
        only_in_right=only_right,
        differing_keys=differing,
        matching_keys=matching,
    )


def format_comparison_report(
    report: ComparisonReport,
    left_label: str = "left",
    right_label: str = "right",
) -> str:
    """Return a human-readable summary of a ComparisonReport."""
    lines: List[str] = []
    lines.append(f"Similarity score : {report.similarity_score:.2%}")
    lines.append(f"Total unique keys: {report.total_unique_keys}")
    lines.append(f"Shared keys      : {len(report.shared_keys)}")
    lines.append(f"  Matching values: {len(report.matching_keys)}")
    lines.append(f"  Differing values: {len(report.differing_keys)}")
    if report.only_in_left:
        lines.append(f"Only in {left_label} ({len(report.only_in_left)}): {', '.join(report.only_in_left)}")
    if report.only_in_right:
        lines.append(f"Only in {right_label} ({len(report.only_in_right)}): {', '.join(report.only_in_right)}")
    return "\n".join(lines)
