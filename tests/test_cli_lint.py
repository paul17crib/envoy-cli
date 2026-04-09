import argparse
import pytest
from io import StringIO
from pathlib import Path
from envoy.cli_lint import build_parser, run_lint


@pytest.fixture
def tmp_env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("APP_NAME=myapp\nDB_HOST=localhost\nSECRET_KEY=supersecret\n")
    return f


def make_args(file, strict=False, check_secrets=False):
    return argparse.Namespace(file=str(file), strict=strict, check_secrets=check_secrets)


def test_lint_clean_file_returns_zero(tmp_env_file):
    out = StringIO()
    result = run_lint(make_args(tmp_env_file), out=out)
    assert result == 0
    assert "No issues found" in out.getvalue()


def test_lint_missing_file_returns_error(tmp_path):
    out = StringIO()
    result = run_lint(make_args(tmp_path / "missing.env"), out=out)
    assert result == 1
    assert "error" in out.getvalue().lower()


def test_lint_invalid_key_returns_error(tmp_path):
    f = tmp_path / ".env"
    f.write_text("1INVALID=value\nGOOD_KEY=ok\n")
    out = StringIO()
    result = run_lint(make_args(f), out=out)
    assert result == 1
    assert "1INVALID" in out.getvalue()


def test_lint_empty_value_produces_warning(tmp_path):
    f = tmp_path / ".env"
    f.write_text("APP_NAME=\nDB_HOST=localhost\n")
    out = StringIO()
    result = run_lint(make_args(f), out=out)
    assert result == 0
    assert "warning" in out.getvalue().lower()


def test_lint_strict_treats_warnings_as_errors(tmp_path):
    f = tmp_path / ".env"
    f.write_text("APP_NAME=\nDB_HOST=localhost\n")
    out = StringIO()
    result = run_lint(make_args(f, strict=True), out=out)
    assert result == 1


def test_lint_check_secrets_warns_on_placeholder(tmp_path):
    f = tmp_path / ".env"
    f.write_text("SECRET_KEY=changeme\nAPP_NAME=myapp\n")
    out = StringIO()
    result = run_lint(make_args(f, check_secrets=True), out=out)
    output = out.getvalue()
    assert "placeholder" in output.lower() or "SECRET_KEY" in output


def test_lint_check_secrets_no_warn_on_real_value(tmp_path):
    f = tmp_path / ".env"
    f.write_text("SECRET_KEY=abc123realvalue\nAPP_NAME=myapp\n")
    out = StringIO()
    result = run_lint(make_args(f, check_secrets=True), out=out)
    assert result == 0
    assert "No issues found" in out.getvalue()


def test_lint_reports_error_and_warning_counts(tmp_path):
    f = tmp_path / ".env"
    f.write_text("1BAD=val\nEMPTY=\n")
    out = StringIO()
    run_lint(make_args(f), out=out)
    output = out.getvalue()
    assert "error(s)" in output
    assert "warning(s)" in output


def test_build_parser_returns_parser():
    parser = build_parser()
    args = parser.parse_args([".env", "--strict"])
    assert args.file == ".env"
    assert args.strict is True
    assert args.check_secrets is False
