import pytest
from io import StringIO
from unittest.mock import patch
from pathlib import Path

from envoy.cli_grep import build_parser, run_grep


@pytest.fixture
def tmp_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "APP_NAME=myapp\n"
        "APP_SECRET=supersecret\n"
        "DATABASE_URL=postgres://localhost/db\n"
        "DEBUG=true\n"
        "API_KEY=abc123\n"
    )
    return str(env_file)


def make_args(pattern, file, keys_only=False, values_only=False,
              no_mask=False, ignore_case=False, count=False):
    parser = build_parser()
    argv = [pattern, "--file", file]
    if keys_only:
        argv.append("--keys-only")
    if values_only:
        argv.append("--values-only")
    if no_mask:
        argv.append("--no-mask")
    if ignore_case:
        argv.append("--ignore-case")
    if count:
        argv.append("--count")
    return parser.parse_args(argv)


def test_grep_finds_matching_key(tmp_env_file):
    out = StringIO()
    args = make_args("APP", tmp_env_file)
    result = run_grep(args, out=out)
    output = out.getvalue()
    assert result == 0
    assert "APP_NAME" in output
    assert "APP_SECRET" in output


def test_grep_finds_matching_value(tmp_env_file):
    out = StringIO()
    args = make_args("true", tmp_env_file, values_only=True)
    result = run_grep(args, out=out)
    output = out.getvalue()
    assert result == 0
    assert "DEBUG" in output


def test_grep_keys_only_ignores_values(tmp_env_file):
    out = StringIO()
    args = make_args("myapp", tmp_env_file, keys_only=True)
    result = run_grep(args, out=out)
    assert result == 1
    assert out.getvalue().strip() == ""


def test_grep_no_match_returns_nonzero(tmp_env_file):
    out = StringIO()
    args = make_args("NONEXISTENT_XYZ", tmp_env_file)
    result = run_grep(args, out=out)
    assert result == 1


def test_grep_masks_sensitive_values_by_default(tmp_env_file):
    out = StringIO()
    args = make_args("API_KEY", tmp_env_file)
    run_grep(args, out=out)
    output = out.getvalue()
    assert "abc123" not in output
    assert "****" in output or "***" in output


def test_grep_no_mask_reveals_values(tmp_env_file):
    out = StringIO()
    args = make_args("API_KEY", tmp_env_file, no_mask=True)
    run_grep(args, out=out)
    output = out.getvalue()
    assert "abc123" in output


def test_grep_count_flag(tmp_env_file):
    out = StringIO()
    args = make_args("APP", tmp_env_file, count=True)
    result = run_grep(args, out=out)
    assert result == 0
    assert out.getvalue().strip() == "2"


def test_grep_ignore_case(tmp_env_file):
    out = StringIO()
    args = make_args("app", tmp_env_file, keys_only=True, ignore_case=True)
    result = run_grep(args, out=out)
    output = out.getvalue()
    assert result == 0
    assert "APP_NAME" in output


def test_grep_invalid_regex_returns_error(tmp_env_file):
    out = StringIO()
    args = make_args("[invalid", tmp_env_file)
    result = run_grep(args, out=out)
    assert result == 1


def test_grep_missing_file_returns_error(tmp_path):
    out = StringIO()
    args = make_args("APP", str(tmp_path / "missing.env"))
    result = run_grep(args, out=out)
    assert result == 1
