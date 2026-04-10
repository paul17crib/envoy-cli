"""Tests for envoy.locker."""

import pytest

pytest.importorskip("cryptography")

from envoy.locker import (
    LockError,
    is_locked,
    lock_env,
    unlock_env,
    LOCK_HEADER,
)


SAMPLE_ENV = {
    "APP_NAME": "myapp",
    "SECRET_KEY": "supersecret",
    "DEBUG": "false",
}


def test_lock_env_produces_header():
    result = lock_env(SAMPLE_ENV, "passphrase123")
    assert result.startswith(LOCK_HEADER)


def test_lock_env_contains_salt_line():
    result = lock_env(SAMPLE_ENV, "passphrase123")
    assert any(line.startswith("# salt:") for line in result.splitlines())


def test_unlock_env_recovers_original():
    locked = lock_env(SAMPLE_ENV, "mypassword")
    recovered = unlock_env(locked, "mypassword")
    assert recovered == SAMPLE_ENV


def test_unlock_env_wrong_passphrase_raises():
    locked = lock_env(SAMPLE_ENV, "correct")
    with pytest.raises(LockError, match="Decryption failed"):
        unlock_env(locked, "wrong")


def test_unlock_env_not_locked_raises():
    with pytest.raises(LockError, match="does not appear"):
        unlock_env("APP=hello\nFOO=bar\n", "pass")


def test_unlock_env_malformed_raises():
    malformed = f"{LOCK_HEADER}\n# no-token-here\n"
    with pytest.raises(LockError):
        unlock_env(malformed, "pass")


def test_is_locked_true_for_locked_content():
    locked = lock_env(SAMPLE_ENV, "x")
    assert is_locked(locked) is True


def test_is_locked_false_for_plain_env():
    assert is_locked("APP=hello\nFOO=bar\n") is False


def test_lock_env_different_passphrases_produce_different_tokens():
    t1 = lock_env(SAMPLE_ENV, "pass1")
    t2 = lock_env(SAMPLE_ENV, "pass2")
    assert t1 != t2


def test_lock_env_same_passphrase_produces_different_tokens():
    """Salt is random, so two locks of the same data differ."""
    t1 = lock_env(SAMPLE_ENV, "same")
    t2 = lock_env(SAMPLE_ENV, "same")
    assert t1 != t2


def test_round_trip_empty_env():
    locked = lock_env({}, "pw")
    assert unlock_env(locked, "pw") == {}
