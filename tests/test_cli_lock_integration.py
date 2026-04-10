"""Integration tests: full lock → unlock round-trip."""

import pytest

pytest.importorskip("cryptography")

from pathlib import Path

from envoy.cli_lock import run_lock
from envoy.locker import is_locked
from envoy.parser import parse_env_string, serialize_env


RICH_ENV = {
    "APP_NAME": "envoy",
    "DATABASE_URL": "postgres://user:pass@localhost/db",
    "SECRET_KEY": "s3cr3t!",
    "API_KEY": "key-abc-123",
    "DEBUG": "true",
    "PORT": "8080",
}


@pytest.fixture()
def rich_env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text(serialize_env(RICH_ENV))
    return p


def make_args(file, unlock=False, output=None, passphrase="integration-pass"):
    class Args:
        pass
    a = Args()
    a.file = str(file)
    a.unlock = unlock
    a.output = output
    a.passphrase = passphrase
    return a


def test_integration_round_trip_preserves_all_keys(rich_env_file):
    run_lock(make_args(rich_env_file))
    assert is_locked(rich_env_file.read_text())

    run_lock(make_args(rich_env_file, unlock=True))
    recovered = parse_env_string(rich_env_file.read_text())
    assert recovered == RICH_ENV


def test_integration_locked_file_is_unreadable_as_plain(rich_env_file):
    run_lock(make_args(rich_env_file, passphrase="secret"))
    raw = rich_env_file.read_text()
    # Sensitive values must not appear in plaintext
    assert "s3cr3t!" not in raw
    assert "key-abc-123" not in raw
    assert "postgres://" not in raw


def test_integration_lock_to_separate_output_does_not_alter_source(rich_env_file, tmp_path):
    locked_path = tmp_path / "locked.env"
    run_lock(make_args(rich_env_file, output=str(locked_path)))
    assert not is_locked(rich_env_file.read_text())
    assert is_locked(locked_path.read_text())
