import pytest
from envoy.auditor import audit_env, format_audit_report, AuditResult


def test_audit_clean_env_returns_no_results():
    env = {"APP_NAME": "myapp", "PORT": "8080", "DEBUG": "false"}
    results = audit_env(env)
    assert results == []


def test_audit_sensitive_empty_value_is_error():
    env = {"SECRET_KEY": ""}
    results = audit_env(env)
    assert len(results) == 1
    assert results[0].level == "error"
    assert results[0].key == "SECRET_KEY"


def test_audit_sensitive_placeholder_is_warning():
    env = {"API_KEY": "changeme"}
    results = audit_env(env)
    assert any(r.level == "warning" and r.key == "API_KEY" for r in results)


def test_audit_sensitive_short_value_is_warning():
    env = {"DB_PASSWORD": "abc"}
    results = audit_env(env)
    assert any(r.level == "warning" and r.key == "DB_PASSWORD" for r in results)


def test_audit_non_sensitive_empty_value_is_info():
    env = {"DESCRIPTION": ""}
    results = audit_env(env)
    assert any(r.level == "info" and r.key == "DESCRIPTION" for r in results)


def test_audit_placeholder_variants():
    placeholders = ["replace_me", "todo", "<your_secret>", "FIXME"]
    for val in placeholders:
        env = {"TOKEN": val}
        results = audit_env(env)
        assert any(r.level == "warning" for r in results), f"Expected warning for placeholder: {val}"


def test_audit_strong_secret_no_issues():
    env = {"SECRET_KEY": "a1b2c3d4e5f6g7h8"}
    results = audit_env(env)
    assert results == []


def test_format_audit_report_no_issues():
    report = format_audit_report([], set())
    assert "No audit issues found" in report


def test_format_audit_report_shows_issues():
    results = [
        AuditResult(key="API_KEY", level="warning", message="Placeholder value."),
        AuditResult(key="SECRET", level="error", message="Empty value."),
    ]
    report = format_audit_report(results, set())
    assert "WARNING" in report
    assert "ERROR" in report
    assert "API_KEY" in report
    assert "SECRET" in report


def test_format_audit_report_masked_keys():
    results = [AuditResult(key="DB_PASSWORD", level="warning", message="Short value.")]
    report = format_audit_report(results, {"DB_PASSWORD"})
    assert "(masked)" in report


def test_audit_multiple_issues():
    env = {
        "SECRET_KEY": "",
        "API_TOKEN": "todo",
        "DB_PASSWORD": "weak",
        "APP_NAME": "myapp",
    }
    results = audit_env(env)
    levels = [r.level for r in results]
    assert "error" in levels
    assert "warning" in levels
