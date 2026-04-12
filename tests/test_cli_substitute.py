"""Tests for envoy.cli_substitute.run_substitute."""

import argparse
import os

import pytest

from envoy.cli_substitute import run_substitute
from envoy.parser import parse_env_file


@pytest.fixture()
def tmp_env_file(tmp_path):
    path = tmp_path / ".env"
    path.write_text("DB_HOST=localhost\nDB_URL=http://localhost:5432\nAPP_NAME=myapp\n")
    return str(path)


def make_args(**kwargs) -> argparse.Namespace:
    defaults = dict(
        file=None,
        find="",
        replace="",
        keys=None,
        regex=False,
        ignore_case=False,
        dry_run=False,
        output=None,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_substitute_replaces_value(tmp_env_file):
    args = make_args(file=tmp_env_file, find="localhost", replace="db.prod.internal")
    rc = run_substitute(args)
    assert rc == 0
    env = parse_env_file(tmp_env_file)
    assert env["DB_HOST"] == "db.prod.internal"
    assert "db.prod.internal" in env["DB_URL"]


def test_substitute_dry_run_does_not_write(tmp_env_file):
    args = make_args(file=tmp_env_file, find="localhost", replace="remote", dry_run=True)
    rc = run_substitute(args)
    assert rc == 0
    env = parse_env_file(tmp_env_file)
    assert env["DB_HOST"] == "localhost"  # unchanged


def test_substitute_keys_filter(tmp_env_file):
    args = make_args(file=tmp_env_file, find="localhost", replace="remote", keys=["DB_HOST"])
    rc = run_substitute(args)
    assert rc == 0
    env = parse_env_file(tmp_env_file)
    assert env["DB_HOST"] == "remote"
    assert "localhost" in env["DB_URL"]  # not touched


def test_substitute_no_match_returns_zero(tmp_env_file):
    args = make_args(file=tmp_env_file, find="NOMATCH", replace="x")
    rc = run_substitute(args)
    assert rc == 0


def test_substitute_missing_file_returns_error(tmp_path):
    args = make_args(file=str(tmp_path / "missing.env"), find="a", replace="b")
    rc = run_substitute(args)
    assert rc == 1


def test_substitute_invalid_regex_returns_error(tmp_env_file):
    args = make_args(file=tmp_env_file, find="[bad", replace="x", regex=True)
    rc = run_substitute(args)
    assert rc == 1


def test_substitute_output_to_separate_file(tmp_env_file, tmp_path):
    out = str(tmp_path / "out.env")
    args = make_args(file=tmp_env_file, find="localhost", replace="prod", output=out)
    rc = run_substitute(args)
    assert rc == 0
    assert os.path.exists(out)
    env = parse_env_file(out)
    assert env["DB_HOST"] == "prod"
    # original unchanged
    orig = parse_env_file(tmp_env_file)
    assert orig["DB_HOST"] == "localhost"


def test_substitute_regex_mode(tmp_env_file):
    args = make_args(file=tmp_env_file, find=r":\d+", replace=":9999", regex=True)
    rc = run_substitute(args)
    assert rc == 0
    env = parse_env_file(tmp_env_file)
    assert env["DB_URL"] == "http://localhost:9999"
