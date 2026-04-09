import argparse
import pytest
from io import StringIO
from envoy.cli_lint import run_lint


@pytest.fixture
def rich_env_file(tmp_path):
    content = (
        "# Application settings\n"
        "APP_NAME=envoy\n"
        "APP_ENV=production\n"
        "\n"
        "# Database\n"
        "DB_HOST=db.example.com\n"
        "DB_PORT=5432\n"
        "DB_PASSWORD=supersecretpassword\n"
        "\n"
        "# Auth\n"
        "SECRET_KEY=changeme\n"
        "API_TOKEN=placeholder\n"
        "EMPTY_VAR=\n"
    )
    f = tmp_path / ".env"
    f.write_text(content)
    return f


def make_args(file, strict=False, check_secrets=False):
    return argparse.Namespace(file=str(file), strict=strict, check_secrets=check_secrets)


def test_integration_clean_run_no_check_secrets(rich_env_file):
    """Without --check-secrets, only structural issues are reported."""
    out = StringIO()
    result = run_lint(make_args(rich_env_file), out=out)
    output = out.getvalue()
    # EMPTY_VAR should trigger a warning but no errors
    assert result == 0
    assert "warning" in output.lower()


def test_integration_check_secrets_flags_placeholders(rich_env_file):
    """With --check-secrets, placeholder values on sensitive keys are flagged."""
    out = StringIO()
    result = run_lint(make_args(rich_env_file, check_secrets=True), out=out)
    output = out.getvalue()
    assert "SECRET_KEY" in output or "API_TOKEN" in output
    assert result == 0  # only warnings, not errors


def test_integration_strict_plus_check_secrets_fails(rich_env_file):
    """Strict mode + check_secrets should return non-zero due to warnings."""
    out = StringIO()
    result = run_lint(make_args(rich_env_file, strict=True, check_secrets=True), out=out)
    assert result == 1


def test_integration_all_good_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("APP_NAME=envoy\nDB_HOST=localhost\nSECRET_KEY=realrandomvalue123\n")
    out = StringIO()
    result = run_lint(make_args(f, strict=True, check_secrets=True), out=out)
    assert result == 0
    assert "No issues found" in out.getvalue()
