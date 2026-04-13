"""Tests for envoy.prefixer module."""

import pytest
from envoy.prefixer import (
    add_prefix,
    remove_prefix,
    list_prefixed_keys,
    rename_prefix,
    PrefixError,
)


@pytest.fixture
def sample_env():
    return {
        "APP_HOST": "localhost",
        "APP_PORT": "8080",
        "DB_URL": "postgres://localhost/mydb",
        "SECRET_KEY": "abc123",
    }


def test_add_prefix_all_keys(sample_env):
    result = add_prefix(sample_env, "TEST_")
    assert "TEST_APP_HOST" in result
    assert "TEST_DB_URL" in result
    assert "TEST_SECRET_KEY" in result
    assert len(result) == len(sample_env)


def test_add_prefix_specific_keys(sample_env):
    result = add_prefix(sample_env, "X_", keys=["DB_URL"])
    assert "X_DB_URL" in result
    assert "APP_HOST" in result
    assert "DB_URL" not in result


def test_add_prefix_preserves_values(sample_env):
    result = add_prefix(sample_env, "PRE_")
    assert result["PRE_APP_PORT"] == "8080"
    assert result["PRE_DB_URL"] == "postgres://localhost/mydb"


def test_add_prefix_empty_raises():
    with pytest.raises(PrefixError, match="empty"):
        add_prefix({"KEY": "val"}, "")


def test_remove_prefix_strips_matching_keys(sample_env):
    result = remove_prefix(sample_env, "APP_")
    assert "HOST" in result
    assert "PORT" in result
    assert "APP_HOST" not in result
    assert "DB_URL" in result


def test_remove_prefix_specific_keys(sample_env):
    result = remove_prefix(sample_env, "APP_", keys=["APP_HOST"])
    assert "HOST" in result
    assert "APP_PORT" in result


def test_remove_prefix_empty_raises():
    with pytest.raises(PrefixError, match="empty"):
        remove_prefix({"KEY": "val"}, "")


def test_remove_prefix_produces_empty_key_raises():
    with pytest.raises(PrefixError, match="empty key"):
        remove_prefix({"PRE_": "val"}, "PRE_")


def test_list_prefixed_keys_returns_matches(sample_env):
    keys = list_prefixed_keys(sample_env, "APP_")
    assert set(keys) == {"APP_HOST", "APP_PORT"}


def test_list_prefixed_keys_no_match_returns_empty(sample_env):
    keys = list_prefixed_keys(sample_env, "MISSING_")
    assert keys == []


def test_rename_prefix_replaces_old_with_new(sample_env):
    result = rename_prefix(sample_env, "APP_", "SVC_")
    assert "SVC_HOST" in result
    assert "SVC_PORT" in result
    assert "APP_HOST" not in result
    assert "DB_URL" in result


def test_rename_prefix_empty_old_raises(sample_env):
    with pytest.raises(PrefixError, match="Old prefix"):
        rename_prefix(sample_env, "", "NEW_")


def test_rename_prefix_preserves_non_matching_values(sample_env):
    result = rename_prefix(sample_env, "DB_", "DATABASE_")
    assert result["DATABASE_URL"] == "postgres://localhost/mydb"
    assert result["APP_HOST"] == "localhost"
