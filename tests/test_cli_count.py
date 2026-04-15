"""Tests for envoy.cli_count."""

import argparse
import io
import pytest
from pathlib import Path

from envoy.cli_count import build_parser, run_count
from envoy.parser import serialize_env


@pytest.fixture
def tmp_env_file(tmp_path):
    env = {"APP_NAME": "myapp", "DB_HOST": "localhost", "API_KEY": "secret-key-here"}
    path = tmp_path / ".env"
    path.write_text(serialize_env(env))
    return path


def make_args(file, pattern, **kwargs):
    defaults = dict(
        file=str(file),
        pattern=pattern,
        keys=None,
        regex=False,
        case_sensitive=False,
        include_keys=False,
        only_matches=False,
        summary=False,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_parser_returns_parser():
    parser = build_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_count_basic_pattern(tmp_env_file):
    out = io.StringIO()
    args = make_args(tmp_env_file, "app")
    rc = run_count(args, out=out)
    assert rc == 0
    output = out.getvalue()
    assert "total:" in output


def test_count_summary_only(tmp_env_file):
    out = io.StringIO()
    args = make_args(tmp_env_file, "key", summary=True)
    rc = run_count(args, out=out)
    assert rc == 0
    lines = out.getvalue().strip().splitlines()
    assert len(lines) == 1
    assert lines[0].isdigit()


def test_count_only_matches_hides_zero_rows(tmp_env_file):
    out = io.StringIO()
    args = make_args(tmp_env_file, "zzznomatch", only_matches=True)
    rc = run_count(args, out=out)
    assert rc == 0
    output = out.getvalue()
    assert "APP_NAME" not in output


def test_count_missing_file_returns_error(tmp_path):
    err = io.StringIO()
    args = make_args(tmp_path / "missing.env", "foo")
    rc = run_count(args, err=err)
    assert rc == 1
    assert "error" in err.getvalue().lower()


def test_count_invalid_regex_returns_error(tmp_env_file):
    err = io.StringIO()
    args = make_args(tmp_env_file, "[", regex=True)
    rc = run_count(args, err=err)
    assert rc == 1
    assert "error" in err.getvalue().lower()


def test_count_restricts_to_specified_keys(tmp_env_file):
    out = io.StringIO()
    args = make_args(tmp_env_file, "local", keys=["DB_HOST"])
    rc = run_count(args, out=out)
    assert rc == 0
    output = out.getvalue()
    assert "APP_NAME" not in output
    assert "DB_HOST" in output
