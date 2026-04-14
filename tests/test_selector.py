"""Tests for envoy.selector."""

import pytest

from envoy.selector import (
    SelectorError,
    get_selected_keys,
    select_by_pattern,
    select_by_value_pattern,
    select_first,
    select_keys,
    select_last,
)


@pytest.fixture()
def sample_env():
    return {
        "APP_NAME": "envoy",
        "APP_ENV": "production",
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "SECRET_KEY": "supersecret",
    }


def test_select_keys_returns_subset(sample_env):
    result = select_keys(sample_env, ["APP_NAME", "DB_HOST"])
    assert result == {"APP_NAME": "envoy", "DB_HOST": "localhost"}


def test_select_keys_preserves_values(sample_env):
    result = select_keys(sample_env, ["SECRET_KEY"])
    assert result["SECRET_KEY"] == "supersecret"


def test_select_keys_missing_key_raises(sample_env):
    with pytest.raises(SelectorError, match="MISSING"):
        select_keys(sample_env, ["MISSING"])


def test_select_keys_missing_ok_skips(sample_env):
    result = select_keys(sample_env, ["APP_NAME", "MISSING"], missing_ok=True)
    assert "APP_NAME" in result
    assert "MISSING" not in result


def test_select_keys_does_not_mutate_original(sample_env):
    original = dict(sample_env)
    select_keys(sample_env, ["APP_NAME"])
    assert sample_env == original


def test_select_by_pattern_matches_prefix(sample_env):
    result = select_by_pattern(sample_env, r"^APP_")
    assert set(result.keys()) == {"APP_NAME", "APP_ENV"}


def test_select_by_pattern_case_insensitive(sample_env):
    result = select_by_pattern(sample_env, r"^app_", case_sensitive=False)
    assert "APP_NAME" in result


def test_select_by_pattern_case_sensitive_no_match(sample_env):
    result = select_by_pattern(sample_env, r"^app_", case_sensitive=True)
    assert result == {}


def test_select_by_pattern_invalid_regex_raises(sample_env):
    with pytest.raises(SelectorError, match="Invalid regex"):
        select_by_pattern(sample_env, r"[invalid")


def test_select_by_value_pattern_matches(sample_env):
    result = select_by_value_pattern(sample_env, r"\d+")
    assert "DB_PORT" in result
    assert "APP_NAME" not in result


def test_select_by_value_pattern_invalid_regex_raises(sample_env):
    with pytest.raises(SelectorError):
        select_by_value_pattern(sample_env, r"[bad")


def test_select_first_returns_n_keys(sample_env):
    result = select_first(sample_env, 2)
    assert len(result) == 2
    assert list(result.keys()) == list(sample_env.keys())[:2]


def test_select_first_zero_returns_empty(sample_env):
    assert select_first(sample_env, 0) == {}


def test_select_first_negative_raises(sample_env):
    with pytest.raises(SelectorError):
        select_first(sample_env, -1)


def test_select_last_returns_n_keys(sample_env):
    result = select_last(sample_env, 2)
    assert len(result) == 2
    assert list(result.keys()) == list(sample_env.keys())[-2:]


def test_select_last_zero_returns_empty(sample_env):
    assert select_last(sample_env, 0) == {}


def test_get_selected_keys_sorted(sample_env):
    selected = select_by_pattern(sample_env, r"^DB_")
    keys = get_selected_keys(sample_env, selected)
    assert keys == sorted(selected.keys())
