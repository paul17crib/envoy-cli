import pytest
import argparse
from io import StringIO
from pathlib import Path
from envoy.cli_unset import build_parser, run_unset
from envoy.sync import save_local


@pytest.fixture
def tmp_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("APP_NAME=envoy\nSECRET_KEY=abc123\nDEBUG=true\n")
    return env_file


def make_args(file, keys, dry_run=False, ignore_missing=False):
    return argparse.Namespace(
        file=str(file),
        keys=keys,
        dry_run=dry_run,
        ignore_missing=ignore_missing,
    )


def test_unset_removes_existing_key(tmp_env_file):
    out, err = StringIO(), StringIO()
    args = make_args(tmp_env_file, ["DEBUG"])
    result = run_unset(args, out=out, err=err)
    assert result == 0
    content = tmp_env_file.read_text()
    assert "DEBUG" not in content
    assert "APP_NAME" in content
    assert "SECRET_KEY" in content


def test_unset_removes_multiple_keys(tmp_env_file):
    out, err = StringIO(), StringIO()
    args = make_args(tmp_env_file, ["APP_NAME", "DEBUG"])
    result = run_unset(args, out=out, err=err)
    assert result == 0
    content = tmp_env_file.read_text()
    assert "APP_NAME" not in content
    assert "DEBUG" not in content
    assert "SECRET_KEY" in content


def test_unset_missing_key_returns_error(tmp_env_file):
    out, err = StringIO(), StringIO()
    args = make_args(tmp_env_file, ["NONEXISTENT"])
    result = run_unset(args, out=out, err=err)
    assert result == 1
    assert "NONEXISTENT" in err.getvalue()


def test_unset_missing_key_with_ignore_flag(tmp_env_file):
    out, err = StringIO(), StringIO()
    args = make_args(tmp_env_file, ["NONEXISTENT"], ignore_missing=True)
    result = run_unset(args, out=out, err=err)
    assert result == 0
    assert "Warning" in out.getvalue()
    assert "NONEXISTENT" in out.getvalue()


def test_unset_dry_run_does_not_write(tmp_env_file):
    original = tmp_env_file.read_text()
    out, err = StringIO(), StringIO()
    args = make_args(tmp_env_file, ["DEBUG"], dry_run=True)
    result = run_unset(args, out=out, err=err)
    assert result == 0
    assert tmp_env_file.read_text() == original
    assert "Dry run" in out.getvalue()
    assert "DEBUG" in out.getvalue()


def test_unset_missing_file_returns_error(tmp_path):
    out, err = StringIO(), StringIO()
    args = make_args(tmp_path / "missing.env", ["KEY"])
    result = run_unset(args, out=out, err=err)
    assert result == 1
    assert "Error" in err.getvalue()


def test_unset_no_keys_to_remove_with_all_missing_and_ignore(tmp_env_file):
    out, err = StringIO(), StringIO()
    args = make_args(tmp_env_file, ["GHOST"], ignore_missing=True)
    result = run_unset(args, out=out, err=err)
    assert result == 0
    assert "No keys to remove" in out.getvalue()


def test_build_parser_returns_parser():
    parser = build_parser()
    assert parser is not None
    args = parser.parse_args(["--file", ".env", "MY_KEY"])
    assert args.keys == ["MY_KEY"]
    assert args.file == ".env"
    assert args.dry_run is False
    assert args.ignore_missing is False
