import argparse
import pytest

from envoy.cli_rename import build_parser, run_rename
from envoy.sync import save_local


@pytest.fixture
def tmp_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("APP_NAME=envoy\nSECRET_KEY=abc123\nDEBUG=true\n")
    return env_file


def make_args(file, old_key, new_key, dry_run=False, force=False):
    return argparse.Namespace(
        file=str(file),
        old_key=old_key,
        new_key=new_key,
        dry_run=dry_run,
        force=force,
    )


def test_rename_existing_key(tmp_env_file):
    args = make_args(tmp_env_file, "APP_NAME", "APPLICATION_NAME")
    result = run_rename(args)
    assert result == 0
    content = tmp_env_file.read_text()
    assert "APPLICATION_NAME=envoy" in content
    assert "APP_NAME" not in content


def test_rename_preserves_other_keys(tmp_env_file):
    args = make_args(tmp_env_file, "APP_NAME", "APPLICATION_NAME")
    run_rename(args)
    content = tmp_env_file.read_text()
    assert "SECRET_KEY=abc123" in content
    assert "DEBUG=true" in content


def test_rename_missing_key_returns_error(tmp_env_file, capsys):
    args = make_args(tmp_env_file, "NONEXISTENT", "NEW_KEY")
    result = run_rename(args)
    assert result == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_rename_missing_file_returns_error(tmp_path, capsys):
    args = make_args(tmp_path / "missing.env", "KEY", "NEW_KEY")
    result = run_rename(args)
    assert result == 1
    captured = capsys.readouterr()
    assert "Error" in captured.err


def test_rename_conflict_without_force_returns_error(tmp_env_file, capsys):
    args = make_args(tmp_env_file, "APP_NAME", "DEBUG")
    result = run_rename(args)
    assert result == 1
    captured = capsys.readouterr()
    assert "already exists" in captured.err


def test_rename_conflict_with_force_overwrites(tmp_env_file):
    args = make_args(tmp_env_file, "APP_NAME", "DEBUG", force=True)
    result = run_rename(args)
    assert result == 0
    content = tmp_env_file.read_text()
    assert "DEBUG=envoy" in content
    assert "APP_NAME" not in content


def test_rename_dry_run_does_not_write(tmp_env_file, capsys):
    original = tmp_env_file.read_text()
    args = make_args(tmp_env_file, "APP_NAME", "APPLICATION_NAME", dry_run=True)
    result = run_rename(args)
    assert result == 0
    assert tmp_env_file.read_text() == original
    captured = capsys.readouterr()
    assert "dry-run" in captured.out
    assert "APPLICATION_NAME" in captured.out


def test_rename_preserves_key_order(tmp_env_file):
    args = make_args(tmp_env_file, "SECRET_KEY", "SECRET_TOKEN")
    run_rename(args)
    lines = [l for l in tmp_env_file.read_text().splitlines() if "=" in l]
    keys = [l.split("=")[0] for l in lines]
    assert keys == ["APP_NAME", "SECRET_TOKEN", "DEBUG"]


def test_build_parser_returns_parser():
    parser = build_parser()
    args = parser.parse_args(["OLD", "NEW", "--file", ".env", "--dry-run"])
    assert args.old_key == "OLD"
    assert args.new_key == "NEW"
    assert args.dry_run is True
