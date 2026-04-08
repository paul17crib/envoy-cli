"""Tests for envoy/cli_diff.py"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from envoy.cli_diff import print_diff, run_diff, _colorize


# --- _colorize ---

def test_colorize_added():
    result = _colorize("+", "+ KEY=val")
    assert "\033[92m" in result
    assert "+ KEY=val" in result


def test_colorize_removed():
    result = _colorize("-", "- KEY=val")
    assert "\033[91m" in result


def test_colorize_changed():
    result = _colorize("~", "~ KEY: 'a' -> 'b'")
    assert "\033[93m" in result


def test_colorize_unknown_symbol():
    result = _colorize("?", "some line")
    assert result == "some line"


# --- print_diff ---

def test_print_diff_empty(capsys):
    print_diff({})
    captured = capsys.readouterr()
    assert "No differences found" in captured.out


def test_print_diff_added(capsys):
    diff = {"NEW_KEY": ("added", None, "value")}
    print_diff(diff, use_color=False)
    captured = capsys.readouterr()
    assert "+ NEW_KEY=value" in captured.out


def test_print_diff_removed(capsys):
    diff = {"OLD_KEY": ("removed", "oldval", None)}
    print_diff(diff, use_color=False)
    captured = capsys.readouterr()
    assert "- OLD_KEY=oldval" in captured.out


def test_print_diff_changed(capsys):
    diff = {"KEY": ("changed", "old", "new")}
    print_diff(diff, use_color=False)
    captured = capsys.readouterr()
    assert "KEY" in captured.out
    assert "old" in captured.out
    assert "new" in captured.out


# --- run_diff ---

@pytest.fixture
def local_env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("APP_NAME=myapp\nSECRET_KEY=abc123\n")
    return str(f)


@pytest.fixture
def remote_env_file(tmp_path):
    f = tmp_path / ".env.remote"
    f.write_text("APP_NAME=myapp\nSECRET_KEY=xyz789\nNEW_VAR=hello\n")
    return str(f)


def test_run_diff_returns_zero_no_diff(tmp_path):
    local = tmp_path / ".env"
    remote = tmp_path / ".env.remote"
    local.write_text("KEY=value\n")
    remote.write_text("KEY=value\n")
    code = run_diff(str(local), str(remote), mask_secrets=False)
    assert code == 0


def test_run_diff_detects_differences(local_env_file, remote_env_file, capsys):
    code = run_diff(local_env_file, remote_env_file, mask_secrets=False, no_color=True)
    captured = capsys.readouterr()
    assert code == 0
    assert "NEW_VAR" in captured.out


def test_run_diff_exit_nonzero_when_diff(local_env_file, remote_env_file):
    code = run_diff(local_env_file, remote_env_file, mask_secrets=False, exit_nonzero=True)
    assert code == 2


def test_run_diff_missing_local(tmp_path, remote_env_file, capsys):
    code = run_diff(str(tmp_path / "missing.env"), remote_env_file)
    assert code == 1
    captured = capsys.readouterr()
    assert "Error" in captured.err


def test_run_diff_missing_remote(local_env_file, tmp_path, capsys):
    code = run_diff(local_env_file, str(tmp_path / "missing.env.remote"))
    assert code == 1
    captured = capsys.readouterr()
    assert "Error" in captured.err
