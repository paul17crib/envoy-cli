import pytest
import argparse
from io import StringIO
from envoy.cli_unset import run_unset
from envoy.sync import load_local


@pytest.fixture
def complex_env(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# Application settings\n"
        "APP_NAME=my-app\n"
        "APP_ENV=production\n"
        "\n"
        "# Secrets\n"
        "DATABASE_URL=postgres://localhost/mydb\n"
        "SECRET_KEY=supersecret\n"
        "API_TOKEN=token123\n"
    )
    return env_file


def make_args(file, keys, dry_run=False, ignore_missing=False):
    return argparse.Namespace(
        file=str(file),
        keys=keys,
        dry_run=dry_run,
        ignore_missing=ignore_missing,
    )


def test_unset_preserves_remaining_keys(complex_env):
    out, err = StringIO(), StringIO()
    args = make_args(complex_env, ["API_TOKEN", "SECRET_KEY"])
    result = run_unset(args, out=out, err=err)
    assert result == 0
    remaining = load_local(str(complex_env))
    assert "API_TOKEN" not in remaining
    assert "SECRET_KEY" not in remaining
    assert remaining["APP_NAME"] == "my-app"
    assert remaining["DATABASE_URL"] == "postgres://localhost/mydb"


def test_unset_partial_missing_with_ignore(complex_env):
    out, err = StringIO(), StringIO()
    args = make_args(complex_env, ["APP_ENV", "MISSING_KEY"], ignore_missing=True)
    result = run_unset(args, out=out, err=err)
    assert result == 0
    remaining = load_local(str(complex_env))
    assert "APP_ENV" not in remaining
    assert "APP_NAME" in remaining
    output = out.getvalue()
    assert "Warning" in output
    assert "MISSING_KEY" in output
    assert "APP_ENV" in output


def test_unset_dry_run_reports_all_keys(complex_env):
    out, err = StringIO(), StringIO()
    args = make_args(complex_env, ["APP_NAME", "APP_ENV"], dry_run=True)
    result = run_unset(args, out=out, err=err)
    assert result == 0
    output = out.getvalue()
    assert "APP_NAME" in output
    assert "APP_ENV" in output
    remaining = load_local(str(complex_env))
    assert "APP_NAME" in remaining
    assert "APP_ENV" in remaining
