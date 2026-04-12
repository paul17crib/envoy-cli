"""Linting rules and checks for .env file contents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy.validator import ValidationIssue, validate_env
from envoy.auditor import audit_env, AuditResult


@dataclass
class LintReport:
    file_path: str
    validation_issues: List[ValidationIssue] = field(default_factory=list)
    audit_results: List[AuditResult] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        errors = sum(1 for i in self.validation_issues if i.level == "error")
        errors += sum(1 for r in self.audit_results if r.level == "error")
        return errors

    @property
    def warning_count(self) -> int:
        warnings = sum(1 for i in self.validation_issues if i.level == "warning")
        warnings += sum(1 for r in self.audit_results if r.level == "warning")
        return warnings

    @property
    def info_count(self) -> int:
        return sum(1 for r in self.audit_results if r.level == "info")

    def is_clean(self) -> bool:
        return self.error_count == 0 and self.warning_count == 0


def lint_env(
    env: Dict[str, str],
    file_path: str = "<unknown>",
    check_secrets: bool = False,
    strict: bool = False,
) -> LintReport:
    """Run all lint checks against an env dict and return a LintReport."""
    report = LintReport(file_path=file_path)

    validation_issues = validate_env(env)
    report.validation_issues = list(validation_issues)

    if check_secrets:
        report.audit_results = audit_env(env)

    if strict:
        for issue in report.validation_issues:
            if issue.level == "warning":
                issue.level = "error"
        for result in report.audit_results:
            if result.level in ("warning", "info"):
                result.level = "error"

    return report


def format_lint_report(report: LintReport, show_info: bool = False) -> str:
    """Format a LintReport as a human-readable string."""
    lines: List[str] = []

    for issue in report.validation_issues:
        lines.append(f"[{issue.level.upper()}] {issue.key}: {issue.message}")

    for result in report.audit_results:
        if result.level == "info" and not show_info:
            continue
        lines.append(f"[{result.level.upper()}] {result.key}: {result.message}")

    if not lines:
        return f"{report.file_path}: no issues found."

    header = f"{report.file_path}: {report.error_count} error(s), {report.warning_count} warning(s)"
    return header + "\n" + "\n".join(lines)
