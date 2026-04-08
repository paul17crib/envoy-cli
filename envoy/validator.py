"""Validation utilities for .env files and their contents."""

import re
from typing import Dict, List, NamedTuple


KEY_PATTERN = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')


class ValidationIssue(NamedTuple):
    key: str
    message: str
    severity: str  # 'error' | 'warning'


def validate_key(key: str) -> bool:
    """Return True if the key is a valid environment variable name."""
    return bool(KEY_PATTERN.match(key))


def validate_env(env: Dict[str, str], required_keys: List[str] = None) -> List[ValidationIssue]:
    """Validate an env dict and return a list of ValidationIssue instances.

    Checks performed:
    - Key naming conventions (errors)
    - Empty values (warnings)
    - Missing required keys (errors)
    """
    issues: List[ValidationIssue] = []

    for key, value in env.items():
        if not validate_key(key):
            issues.append(
                ValidationIssue(
                    key=key,
                    message=f"Invalid key name '{key}': must match [A-Za-z_][A-Za-z0-9_]*",
                    severity='error',
                )
            )

        if value == '':
            issues.append(
                ValidationIssue(
                    key=key,
                    message=f"Key '{key}' has an empty value",
                    severity='warning',
                )
            )

    if required_keys:
        for req in required_keys:
            if req not in env:
                issues.append(
                    ValidationIssue(
                        key=req,
                        message=f"Required key '{req}' is missing",
                        severity='error',
                    )
                )

    return issues


def has_errors(issues: List[ValidationIssue]) -> bool:
    """Return True if any issue has severity 'error'."""
    return any(i.severity == 'error' for i in issues)


def format_issues(issues: List[ValidationIssue]) -> str:
    """Return a human-readable summary of validation issues."""
    if not issues:
        return 'No issues found.'
    lines = []
    for issue in issues:
        prefix = '[ERROR]' if issue.severity == 'error' else '[WARN] '
        lines.append(f"{prefix} {issue.message}")
    return '\n'.join(lines)
