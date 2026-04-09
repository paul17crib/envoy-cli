"""Tests for envoy/cli_pull.py"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import argparse

from envoy.cli_pull import run_pull, build_parser


@pytest.fixture
def base_args(tmp_path):
    remote = tmp_path / "remote.env"
    local = tmp_path / ".env"
    remote.write_text("APP_NAME=envoy\nSECRET_KEY=abc123\n")
    return argparse.Namespace(
        remote=str(remote),
        local=str(local),
        merge=False,
        validate=False,
        show=False,
        mask=False,
    )


def test_pull_creates_local_file(base_args, tmp_path):
    local = Path(base_args.local)
    assert not local.exists()
    result = run_pull(base_args)
    assert result == 0
    assert local.exists()
    content = local.read_text()
    assert "APP_NAME" in content
    assert "SECRET_KEY" in content


def test_pull_overwrites_local_file(base_args, tmp_path):
    local = Path(base_args.local)
    local.write_text("OLD_VAR=old\n")
    result = run_pull(base_args)
    assert result == 0
    content = local.read_text()
    assert "OLD_VAR" not in content
    assert "APP_NAME" in content


def test_pull_merge_keeps_local_keys(base_args, tmp_path):
    local = Path(base_args.local)
    local.write_text("LOCAL_ONLY=yes\nAPP_NAME=old\n")
    base_args.merge = True
    result = run_pull(base_args)
    assert result == 0
    content = local.read_text()
    assert "LOCAL_ONLY" in content
    assert "APP_NAME" in content


def test_pull_missing_remote_returns_error(base_args, tmp_path):
    base_args.remote = str(tmp_path / "nonexistent.env")
    result = run_pull(base_args)
    assert result == 1


def test_pull_with_validate_passes(base_args):
    base_args.validate = True
    result = run_pull(base_args)
    assert result == 0


def test_pull_with_validate_fails_on_bad_key(base_args, tmp_path):
    bad_remote = tmp_path / "bad_remote.env"
    bad_remote.write_text("123INVALID=value\n")
    base_args.remote = str(bad_remote)
    base_args.validate = True
    result = run_pull(base_args)
    assert result == 1


def test_pull_show_does_not_crash(base_args, capsys):
    base_args.show = True
    result = run_pull(base_args)
    assert result == 0
    captured = capsys.readouterr()
    assert "APP_NAME" in captured.out


def test_pull_show_with_mask_hides_secret(base_args, capsys):
    base_args.show = True
    base_args.mask = True
    result = run_pull(base_args)
    assert result == 0
    captured = capsys.readouterr()
    assert "abc123" not in captured.out


def test_build_parser_returns_parser():
    parser = build_parser()
    args = parser.parse_args(["remote.env", "--local", ".env", "--merge", "--show", "--mask"])
    assert args.remote == "remote.env"
    assert args.local == ".env"
    assert args.merge is True
    assert args.show is True
    assert args.mask is True
