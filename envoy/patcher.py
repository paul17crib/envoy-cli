"""Patch (in-place update) multiple keys in an env dict from a patch file or dict."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PatchResult:
    applied: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    added: List[str] = field(default_factory=list)

    @property
    def total_changed(self) -> int:
        return len(self.applied) + len(self.added)


def patch_env(
    base: Dict[str, str],
    patch: Dict[str, str],
    *,
    add_new: bool = True,
    overwrite: bool = True,
    keys: Optional[List[str]] = None,
) -> tuple[Dict[str, str], PatchResult]:
    """Apply patch dict onto base, returning a new dict and a PatchResult.

    Args:
        base: The original env mapping.
        patch: Key/value pairs to apply.
        add_new: If False, keys not present in base are skipped.
        overwrite: If False, existing keys are not overwritten.
        keys: Optional allow-list of keys to patch; others are ignored.
    """
    result = dict(base)
    report = PatchResult()

    for key, value in patch.items():
        if keys is not None and key not in keys:
            report.skipped.append(key)
            continue

        if key in base:
            if not overwrite:
                report.skipped.append(key)
                continue
            result[key] = value
            report.applied.append(key)
        else:
            if not add_new:
                report.skipped.append(key)
                continue
            result[key] = value
            report.added.append(key)

    return result, report


def format_patch_report(report: PatchResult) -> str:
    lines: List[str] = []
    if report.applied:
        lines.append(f"Updated : {', '.join(sorted(report.applied))}")
    if report.added:
        lines.append(f"Added   : {', '.join(sorted(report.added))}")
    if report.skipped:
        lines.append(f"Skipped : {', '.join(sorted(report.skipped))}")
    if not lines:
        lines.append("No changes applied.")
    return "\n".join(lines)
