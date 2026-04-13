"""Tests for envoy/digester.py."""

import pytest

from envoy.digester import (
    DigestError,
    SUPPORTED_ALGORITHMS,
    changed_keys,
    digest_env,
    digest_file,
    envs_match,
)


# ---------------------------------------------------------------------------
# digest_env
# ---------------------------------------------------------------------------

def test_digest_env_returns_string():
    result = digest_env({"KEY": "value"})
    assert isinstance(result, str)
    assert len(result) > 0


def test_digest_env_sha256_length():
    result = digest_env({"A": "1"}, algorithm="sha256")
    assert len(result) == 64


def test_digest_env_md5_length():
    result = digest_env({"A": "1"}, algorithm="md5")
    assert len(result) == 32


def test_digest_env_order_independent():
    a = digest_env({"X": "1", "Y": "2"})
    b = digest_env({"Y": "2", "X": "1"})
    assert a == b


def test_digest_env_different_values_differ():
    a = digest_env({"KEY": "hello"})
    b = digest_env({"KEY": "world"})
    assert a != b


def test_digest_env_empty_dict():
    result = digest_env({})
    assert isinstance(result, str)
    assert len(result) == 64  # sha256


def test_digest_env_unsupported_algorithm_raises():
    with pytest.raises(DigestError, match="Unsupported algorithm"):
        digest_env({"K": "v"}, algorithm="crc32")


def test_digest_env_all_supported_algorithms():
    env = {"FOO": "bar", "BAZ": "qux"}
    for algo in SUPPORTED_ALGORITHMS:
        result = digest_env(env, algorithm=algo)
        assert isinstance(result, str)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# digest_file
# ---------------------------------------------------------------------------

def test_digest_file_returns_string(tmp_path):
    f = tmp_path / "sample.env"
    f.write_text("KEY=value\nOTHER=123\n")
    result = digest_file(str(f))
    assert isinstance(result, str)
    assert len(result) == 64


def test_digest_file_changes_when_content_changes(tmp_path):
    f = tmp_path / "sample.env"
    f.write_text("KEY=original\n")
    before = digest_file(str(f))
    f.write_text("KEY=modified\n")
    after = digest_file(str(f))
    assert before != after


def test_digest_file_unsupported_algorithm_raises(tmp_path):
    f = tmp_path / "x.env"
    f.write_text("A=1\n")
    with pytest.raises(DigestError):
        digest_file(str(f), algorithm="sha3_256")


# ---------------------------------------------------------------------------
# envs_match
# ---------------------------------------------------------------------------

def test_envs_match_identical_dicts():
    env = {"A": "1", "B": "2"}
    assert envs_match(env, dict(env)) is True


def test_envs_match_different_dicts():
    assert envs_match({"A": "1"}, {"A": "2"}) is False


def test_envs_match_empty_dicts():
    assert envs_match({}, {}) is True


# ---------------------------------------------------------------------------
# changed_keys
# ---------------------------------------------------------------------------

def test_changed_keys_detects_value_change():
    result = changed_keys({"A": "old"}, {"A": "new"})
    assert result == {"A": ("old", "new")}


def test_changed_keys_detects_added_key():
    result = changed_keys({}, {"NEW": "val"})
    assert result == {"NEW": (None, "val")}


def test_changed_keys_detects_removed_key():
    result = changed_keys({"GONE": "bye"}, {})
    assert result == {"GONE": ("bye", None)}


def test_changed_keys_ignores_unchanged():
    result = changed_keys({"A": "same", "B": "x"}, {"A": "same", "B": "y"})
    assert "A" not in result
    assert "B" in result


def test_changed_keys_empty_envs_returns_empty():
    assert changed_keys({}, {}) == {}
