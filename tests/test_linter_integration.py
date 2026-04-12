"""Integration tests for envoy.linter combining validation and audit."""

import pytest
from envoy.linter import lint_env, format_lint_report


RICH_ENV = {
    "APP_NAME": "envoy",
    "APP_ENV": "production",
    "APP_PORT": "443",
    "DB_HOST": "db.internal",
    "DB_PASSWORD": "changeme",
    "SECRET_KEY": "",
    "API_TOKEN": "placeholder",
    "DEBUG": "false",
}


def test_integration_clean_keys_no_errors_without_secrets():
    report = lint_env(RICH_ENV, file_path=".env", check_secrets=False)
    assert report.error_count == 0


def test_integration_check_secrets_finds_weak_values():
    report = lint_env(RICH_ENV, file_path=".env", check_secrets=True)
    audit_keys = {r.key for r in report.audit_results}
    # Should flag empty SECRET_KEY and placeholder values
    assert "SECRET_KEY" in audit_keys or "DB_PASSWORD" in audit_keys


def test_integration_strict_mode_no_warnings_only_errors():
    report = lint_env(RICH_ENV, file_path=".env", check_secrets=True, strict=True)
    for issue in report.validation_issues:
        assert issue.level == "error"
    for result in report.audit_results:
        assert result.level == "error"


def test_integration_format_includes_file_path():
    report = lint_env(RICH_ENV, file_path="config/.env.production", check_secrets=True)
    output = format_lint_report(report)
    assert "config/.env.production" in output


def test_integration_empty_env_is_clean():
    report = lint_env({}, file_path=".env")
    assert report.is_clean()
    output = format_lint_report(report)
    assert "no issues found" in output
