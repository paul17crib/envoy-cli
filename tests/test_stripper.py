"""Tests for envoy.stripper."""

import pytest
from envoy.stripper import (
    StripError,
    strip_keys,
    strip_by_pattern,
    strip_empty,
    get_stripped_keys,
)


@pytest.fixture
def sample_env():
    return {
        "APP_NAME": "myapp",
        "APP_ENV": "production",
        "DB_HOST": "localhost",
        "DB_PASSWORD": "s3cr3t",
        "DEBUG": "",
        "LOG_LEVEL": "info",
    }


def test_strip_keys_removes_specified(sample_env):
    result = strip_keys(sample_env, ["DEBUG"])
    assert "DEBUG" not in result
    assert len(result) == len(sample_env) - 1


def test_strip_keys_removes_multiple(sample_env):
    result = strip_keys(sample_env, ["APP_NAME", "DB_HOST"])
    assert "APP_NAME" not in result
    assert "DB_HOST" not in result
    assert "APP_ENV" in result


def test_strip_keys_does_not_mutate_original(sample_env):
    original_copy = dict(sample_env)
    strip_keys(sample_env, ["DEBUG"])
    assert sample_env == original_copy


def test_strip_keys_missing_key_raises(sample_env):
    with pytest.raises(StripError, match="Key not found"):
        strip_keys(sample_env, ["NONEXISTENT"])


def test_strip_keys_missing_ok_skips(sample_env):
    result = strip_keys(sample_env, ["NONEXISTENT"], missing_ok=True)
    assert result == sample_env


def test_strip_keys_empty_list_raises(sample_env):
    with pytest.raises(StripError, match="At least one key"):
        strip_keys(sample_env, [])


def test_strip_by_pattern_removes_matching(sample_env):
    result = strip_by_pattern(sample_env, r"^APP_")
    assert "APP_NAME" not in result
    assert "APP_ENV" not in result
    assert "DB_HOST" in result


def test_strip_by_pattern_case_insensitive_default(sample_env):
    result = strip_by_pattern(sample_env, r"^app_")
    assert "APP_NAME" not in result
    assert "APP_ENV" not in result


def test_strip_by_pattern_case_sensitive(sample_env):
    result = strip_by_pattern(sample_env, r"^app_", case_sensitive=True)
    # lowercase pattern should NOT match uppercase keys
    assert "APP_NAME" in result


def test_strip_by_pattern_invalid_regex_raises(sample_env):
    with pytest.raises(StripError, match="Invalid pattern"):
        strip_by_pattern(sample_env, r"[invalid")


def test_strip_by_pattern_no_match_returns_full(sample_env):
    result = strip_by_pattern(sample_env, r"^NOPE_")
    assert result == sample_env


def test_strip_empty_removes_blank_values(sample_env):
    result = strip_empty(sample_env)
    assert "DEBUG" not in result
    assert "APP_NAME" in result


def test_strip_empty_does_not_mutate(sample_env):
    original_copy = dict(sample_env)
    strip_empty(sample_env)
    assert sample_env == original_copy


def test_get_stripped_keys_returns_diff(sample_env):
    stripped = strip_keys(sample_env, ["APP_NAME", "DEBUG"])
    removed = get_stripped_keys(sample_env, stripped)
    assert set(removed) == {"APP_NAME", "DEBUG"}


def test_get_stripped_keys_empty_when_identical(sample_env):
    removed = get_stripped_keys(sample_env, dict(sample_env))
    assert removed == []
