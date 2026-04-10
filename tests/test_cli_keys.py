"""Tests for envoy/cli_keys.py"""

import io
import pytest
from pathlib import Path
from types import SimpleNamespace

from envoy.cli_keys import build_parser, run_keys


@pytest.fixture
def tmp_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "APP_NAME=myapp\n"
        "APP_PORT=8080\n"
        "SECRET_KEY=supersecret\n"
        "DATABASE_URL=postgres://localhost/db\n"
        "DEBUG=true\n"
    )
    return str(env_file)


def make_args(file, prefix=None, sensitive_only=False, count=False, no_header=False):
    return SimpleNamespace(
        file=file,
        prefix=prefix,
        sensitive_only=sensitive_only,
        count=count,
        no_header=no_header,
    )


def test_list_all_keys(tmp_env_file):
    out = io.StringIO()
    result = run_keys(make_args(tmp_env_file), out=out)
    output = out.getvalue()
    assert result == 0
    assert "APP_NAME" in output
    assert "APP_PORT" in output
    assert "SECRET_KEY" in output
    assert "DATABASE_URL" in output
    assert "DEBUG" in output


def test_list_keys_with_prefix(tmp_env_file):
    out = io.StringIO()
    result = run_keys(make_args(tmp_env_file, prefix="APP_"), out=out)
    output = out.getvalue()
    assert result == 0
    assert "APP_NAME" in output
    assert "APP_PORT" in output
    assert "SECRET_KEY" not in output
    assert "DATABASE_URL" not in output


def test_prefix_is_case_insensitive(tmp_env_file):
    out = io.StringIO()
    result = run_keys(make_args(tmp_env_file, prefix="app_"), out=out)
    output = out.getvalue()
    assert result == 0
    assert "APP_NAME" in output
    assert "APP_PORT" in output


def test_sensitive_only_flag(tmp_env_file):
    out = io.StringIO()
    result = run_keys(make_args(tmp_env_file, sensitive_only=True), out=out)
    output = out.getvalue()
    assert result == 0
    assert "SECRET_KEY" in output
    assert "DATABASE_URL" in output
    assert "APP_NAME" not in output
    assert "DEBUG" not in output


def test_count_flag_returns_number(tmp_env_file):
    out = io.StringIO()
    result = run_keys(make_args(tmp_env_file, count=True), out=out)
    output = out.getvalue().strip()
    assert result == 0
    assert output == "5"


def test_count_with_prefix(tmp_env_file):
    out = io.StringIO()
    result = run_keys(make_args(tmp_env_file, prefix="APP_", count=True), out=out)
    output = out.getvalue().strip()
    assert result == 0
    assert output == "2"


def test_no_header_suppresses_header(tmp_env_file):
    out = io.StringIO()
    run_keys(make_args(tmp_env_file, no_header=True), out=out)
    output = out.getvalue()
    assert "KEY" not in output
    assert "---" not in output


def test_missing_file_returns_error(tmp_path):
    out = io.StringIO()
    result = run_keys(make_args(str(tmp_path / "missing.env")), out=out)
    assert result == 1


def test_build_parser_returns_parser():
    parser = build_parser()
    args = parser.parse_args(["myfile.env", "--prefix", "DB_", "--count"])
    assert args.file == "myfile.env"
    assert args.prefix == "DB_"
    assert args.count is True
