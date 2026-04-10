"""Tests for envoy.trimmer."""

import pytest
from envoy.trimmer import (
    trim_by_prefix,
    trim_by_suffix,
    trim_by_pattern,
    trim_keys,
    get_trimmed_keys,
)


@pytest.fixture
def sample_env():
    return {
        "APP_NAME": "myapp",
        "APP_DEBUG": "true",
        "DB_HOST": "localhost",
        "DB_PASSWORD": "secret",
        "SECRET_KEY": "abc123",
        "LOG_LEVEL": "info",
    }


def test_trim_by_prefix_removes_matching_keys(sample_env):
    result = trim_by_prefix(sample_env, "APP_")
    assert "APP_NAME" not in result
    assert "APP_DEBUG" not in result
    assert "DB_HOST" in result


def test_trim_by_prefix_case_insensitive_by_default(sample_env):
    result = trim_by_prefix(sample_env, "app_")
    assert "APP_NAME" not in result
    assert "APP_DEBUG" not in result


def test_trim_by_prefix_case_sensitive(sample_env):
    result = trim_by_prefix(sample_env, "app_", case_sensitive=True)
    # lowercase prefix won't match uppercase keys
    assert "APP_NAME" in result
    assert "APP_DEBUG" in result


def test_trim_by_prefix_no_match_returns_full_env(sample_env):
    result = trim_by_prefix(sample_env, "UNUSED_")
    assert result == sample_env


def test_trim_by_suffix_removes_matching_keys(sample_env):
    result = trim_by_suffix(sample_env, "_KEY")
    assert "SECRET_KEY" not in result
    assert "APP_NAME" in result


def test_trim_by_suffix_case_insensitive_by_default(sample_env):
    result = trim_by_suffix(sample_env, "_key")
    assert "SECRET_KEY" not in result


def test_trim_by_suffix_no_match_returns_full_env(sample_env):
    result = trim_by_suffix(sample_env, "_NOTHING")
    assert result == sample_env


def test_trim_by_pattern_removes_matching_keys(sample_env):
    result = trim_by_pattern(sample_env, r"^DB_")
    assert "DB_HOST" not in result
    assert "DB_PASSWORD" not in result
    assert "APP_NAME" in result


def test_trim_by_pattern_complex_pattern(sample_env):
    result = trim_by_pattern(sample_env, r"(SECRET|PASSWORD)")
    assert "SECRET_KEY" not in result
    assert "DB_PASSWORD" not in result
    assert "DB_HOST" in result


def test_trim_by_pattern_no_match_returns_full_env(sample_env):
    result = trim_by_pattern(sample_env, r"^NOMATCH")
    assert result == sample_env


def test_trim_keys_removes_listed_keys(sample_env):
    result = trim_keys(sample_env, ["APP_NAME", "LOG_LEVEL"])
    assert "APP_NAME" not in result
    assert "LOG_LEVEL" not in result
    assert "DB_HOST" in result


def test_trim_keys_ignores_missing_keys(sample_env):
    result = trim_keys(sample_env, ["NONEXISTENT"])
    assert result == sample_env


def test_trim_does_not_mutate_original(sample_env):
    original_copy = dict(sample_env)
    trim_by_prefix(sample_env, "APP_")
    assert sample_env == original_copy


def test_get_trimmed_keys_returns_removed(sample_env):
    trimmed = trim_by_prefix(sample_env, "APP_")
    removed = get_trimmed_keys(sample_env, trimmed)
    assert set(removed) == {"APP_NAME", "APP_DEBUG"}


def test_get_trimmed_keys_empty_when_nothing_removed(sample_env):
    removed = get_trimmed_keys(sample_env, sample_env)
    assert removed == []
