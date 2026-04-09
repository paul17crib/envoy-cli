"""Tests for envoy/cli_list.py"""

import pytest
import argparse
from io import StringIO
from pathlib import Path
from envoy.cli_list import build_parser, run_list


@pytest.fixture
def tmp_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "APP_NAME=myapp\n"
        "SECRET_KEY=supersecret\n"
        "DB_PASSWORD=dbpass123\n"
        "DEBUG=true\n"
        "APP_VERSION=1.0.0\n"
    )
    return env_file


def make_args(file, keys_only=False, no_mask=False, prefix=None):
    return argparse.Namespace(
        file=str(file),
        keys_only=keys_only,
        no_mask=no_mask,
        prefix=prefix,
    )


def test_list_displays_table(tmp_env_file):
    out = StringIO()
    args = make_args(tmp_env_file)
    result = run_list(args, out=out)
    assert result == 0
    output = out.getvalue()
    assert "APP_NAME" in output
    assert "DEBUG" in output


def test_list_masks_sensitive_values_by_default(tmp_env_file):
    out = StringIO()
    args = make_args(tmp_env_file)
    result = run_list(args, out=out)
    assert result == 0
    output = out.getvalue()
    assert "supersecret" not in output
    assert "dbpass123" not in output


def test_list_no_mask_reveals_values(tmp_env_file):
    out = StringIO()
    args = make_args(tmp_env_file, no_mask=True)
    result = run_list(args, out=out)
    assert result == 0
    output = out.getvalue()
    assert "supersecret" in output
    assert "dbpass123" in output


def test_list_keys_only(tmp_env_file):
    out = StringIO()
    args = make_args(tmp_env_file, keys_only=True)
    result = run_list(args, out=out)
    assert result == 0
    lines = [l.strip() for l in out.getvalue().splitlines() if l.strip()]
    assert "APP_NAME" in lines
    assert "SECRET_KEY" in lines
    assert "supersecret" not in lines


def test_list_keys_only_sorted(tmp_env_file):
    out = StringIO()
    args = make_args(tmp_env_file, keys_only=True)
    run_list(args, out=out)
    lines = [l.strip() for l in out.getvalue().splitlines() if l.strip()]
    assert lines == sorted(lines)


def test_list_prefix_filter(tmp_env_file):
    out = StringIO()
    args = make_args(tmp_env_file, keys_only=True, prefix="APP_")
    result = run_list(args, out=out)
    assert result == 0
    lines = [l.strip() for l in out.getvalue().splitlines() if l.strip()]
    assert all(k.startswith("APP_") for k in lines)
    assert "DEBUG" not in lines
    assert "SECRET_KEY" not in lines


def test_list_prefix_no_match(tmp_env_file):
    out = StringIO()
    args = make_args(tmp_env_file, prefix="NONEXISTENT_")
    result = run_list(args, out=out)
    assert result == 0
    assert "No keys found." in out.getvalue()


def test_list_missing_file_returns_error(tmp_path):
    out = StringIO()
    args = make_args(tmp_path / "missing.env")
    result = run_list(args, out=out)
    assert result == 1
    assert "Error" in out.getvalue()


def test_build_parser_returns_parser():
    parser = build_parser()
    args = parser.parse_args(["--file", ".env", "--keys-only"])
    assert args.keys_only is True
    assert args.file == ".env"
