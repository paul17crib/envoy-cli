"""Tests for envoy.cli_lock."""

import pytest

pytest.importorskip("cryptography")

from pathlib import Path
from unittest.mock import patch

from envoy.cli_lock import run_lock
from envoy.locker import is_locked, lock_env
from envoy.parser import serialize_env


SAMPLE = {"KEY": "value", "SECRET_KEY": "abc123"}


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text(serialize_env(SAMPLE))
    return p


def make_args(file, unlock=False, output=None, passphrase="testpass"):
    class Args:
        pass
    a = Args()
    a.file = str(file)
    a.unlock = unlock
    a.output = output
    a.passphrase = passphrase
    return a


def test_lock_creates_locked_file(env_file):
    rc = run_lock(make_args(env_file))
    assert rc == 0
    assert is_locked(env_file.read_text())


def test_lock_output_to_separate_file(env_file, tmp_path):
    out = tmp_path / "locked.env"
    rc = run_lock(make_args(env_file, output=str(out)))
    assert rc == 0
    assert is_locked(out.read_text())
    assert not is_locked(env_file.read_text())  # original untouched


def test_unlock_recovers_original(env_file):
    run_lock(make_args(env_file, passphrase="pw"))
    rc = run_lock(make_args(env_file, unlock=True, passphrase="pw"))
    assert rc == 0
    assert not is_locked(env_file.read_text())


def test_lock_already_locked_returns_error(env_file):
    run_lock(make_args(env_file))
    rc = run_lock(make_args(env_file))
    assert rc == 1


def test_unlock_not_locked_returns_error(env_file):
    rc = run_lock(make_args(env_file, unlock=True))
    assert rc == 1


def test_unlock_wrong_passphrase_returns_error(env_file):
    run_lock(make_args(env_file, passphrase="correct"))
    rc = run_lock(make_args(env_file, unlock=True, passphrase="wrong"))
    assert rc == 1


def test_missing_file_returns_error(tmp_path):
    rc = run_lock(make_args(tmp_path / "missing.env"))
    assert rc == 1


def test_empty_passphrase_returns_error(env_file):
    rc = run_lock(make_args(env_file, passphrase=""))
    assert rc == 1
