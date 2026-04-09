import argparse
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from envoy.cli_push import run_push, build_parser
from envoy.remote import FileRemoteProvider


@pytest.fixture
def base_args(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("APP_NAME=envoy\nDEBUG=false\n")
    args = argparse.Namespace(
        file=str(env_file),
        remote=str(tmp_path / "remote.env"),
        dry_run=False,
        skip_validation=False,
        show_values=False,
    )
    return args


def test_push_writes_to_remote(tmp_path, base_args):
    remote_path = tmp_path / "remote.env"
    base_args.remote = str(remote_path)
    provider = FileRemoteProvider(str(remote_path))
    result = run_push(base_args, provider=provider)
    assert result == 0
    assert remote_path.exists()
    content = remote_path.read_text()
    assert "APP_NAME" in content


def test_push_missing_local_file_returns_error(tmp_path):
    args = argparse.Namespace(
        file=str(tmp_path / "nonexistent.env"),
        remote=str(tmp_path / "remote.env"),
        dry_run=False,
        skip_validation=True,
        show_values=False,
    )
    result = run_push(args)
    assert result == 1


def test_push_dry_run_does_not_write(tmp_path, base_args, capsys):
    remote_path = tmp_path / "remote.env"
    base_args.remote = str(remote_path)
    base_args.dry_run = True
    result = run_push(base_args)
    assert result == 0
    assert not remote_path.exists()
    captured = capsys.readouterr()
    assert "dry-run" in captured.out
    assert "APP_NAME" in captured.out


def test_push_dry_run_masks_sensitive_values(tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text("SECRET_KEY=supersecret\nNAME=envoy\n")
    remote_path = tmp_path / "remote.env"
    args = argparse.Namespace(
        file=str(env_file),
        remote=str(remote_path),
        dry_run=True,
        skip_validation=True,
        show_values=False,
    )
    result = run_push(args)
    assert result == 0
    captured = capsys.readouterr()
    assert "supersecret" not in captured.out
    assert "SECRET_KEY" in captured.out


def test_push_validation_error_blocks_push(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("123INVALID=value\n")
    remote_path = tmp_path / "remote.env"
    args = argparse.Namespace(
        file=str(env_file),
        remote=str(remote_path),
        dry_run=False,
        skip_validation=False,
        show_values=False,
    )
    result = run_push(args)
    assert result == 1
    assert not remote_path.exists()


def test_push_skip_validation_bypasses_check(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("123INVALID=value\n")
    remote_path = tmp_path / "remote.env"
    args = argparse.Namespace(
        file=str(env_file),
        remote=str(remote_path),
        dry_run=False,
        skip_validation=True,
        show_values=False,
    )
    provider = FileRemoteProvider(str(remote_path))
    result = run_push(args, provider=provider)
    assert result == 0


def test_build_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["--remote", "remote.env"])
    assert args.file == ".env"
    assert args.dry_run is False
    assert args.skip_validation is False
    assert args.show_values is False
