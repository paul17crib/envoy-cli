"""Tests for envoy.linter module."""

import pytest
from envoy.linter import lint_env, format_lint_report, LintReport


CLEAN_ENV = {
    "APP_NAME": "myapp",
    "APP_PORT": "8080",
    "DATABASE_URL": "postgres://localhost/db",
}

INVALID_KEY_ENV = {
    "APP_NAME": "myapp",
    "123INVALID": "bad",
}

SECRET_PLACEHOLDER_ENV = {
    "APP_NAME": "myapp",
    "SECRET_KEY": "changeme",
    "API_TOKEN": "",
}


def test_lint_clean_env_returns_clean_report():
    report = lint_env(CLEAN_ENV, file_path=".env")
    assert report.is_clean()
    assert report.error_count == 0
    assert report.warning_count == 0


def test_lint_invalid_key_produces_error():
    report = lint_env(INVALID_KEY_ENV, file_path=".env")
    assert report.error_count > 0
    keys = [i.key for i in report.validation_issues]
    assert "123INVALID" in keys


def test_lint_check_secrets_flags_placeholder():
    report = lint_env(SECRET_PLACEHOLDER_ENV, file_path=".env", check_secrets=True)
    audit_keys = [r.key for r in report.audit_results]
    assert "SECRET_KEY" in audit_keys or "API_TOKEN" in audit_keys


def test_lint_no_check_secrets_skips_audit():
    report = lint_env(SECRET_PLACEHOLDER_ENV, file_path=".env", check_secrets=False)
    assert report.audit_results == []


def test_lint_strict_promotes_warnings_to_errors():
    report = lint_env(SECRET_PLACEHOLDER_ENV, file_path=".env", check_secrets=True, strict=True)
    for result in report.audit_results:
        assert result.level == "error"


def test_lint_report_file_path_stored():
    report = lint_env(CLEAN_ENV, file_path="/project/.env")
    assert report.file_path == "/project/.env"


def test_format_lint_report_clean():
    report = lint_env(CLEAN_ENV, file_path=".env")
    output = format_lint_report(report)
    assert "no issues found" in output


def test_format_lint_report_shows_errors():
    report = lint_env(INVALID_KEY_ENV, file_path=".env")
    output = format_lint_report(report)
    assert "ERROR" in output
    assert "123INVALID" in output


def test_format_lint_report_header_counts():
    report = lint_env(INVALID_KEY_ENV, file_path=".env")
    output = format_lint_report(report)
    assert "error(s)" in output


def test_format_lint_report_info_hidden_by_default():
    report = lint_env(SECRET_PLACEHOLDER_ENV, file_path=".env", check_secrets=True)
    output = format_lint_report(report, show_info=False)
    lines = output.splitlines()
    assert not any("[INFO]" in line for line in lines)


def test_lint_report_info_count():
    report = LintReport(file_path=".env")
    from envoy.auditor import AuditResult
    report.audit_results = [AuditResult(key="FOO", level="info", message="ok")]
    assert report.info_count == 1
    assert report.warning_count == 0
    assert report.error_count == 0
