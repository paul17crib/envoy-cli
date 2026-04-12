"""Tests for envoy.substitutor."""

import pytest

from envoy.substitutor import (
    SubstitutionError,
    get_substituted_keys,
    substitute_env,
    substitute_value,
)


# ---------------------------------------------------------------------------
# substitute_value
# ---------------------------------------------------------------------------

def test_substitute_value_simple_replace():
    assert substitute_value("hello world", "world", "earth") == "hello earth"


def test_substitute_value_no_match_unchanged():
    assert substitute_value("hello", "xyz", "abc") == "hello"


def test_substitute_value_regex_replace():
    result = substitute_value("foo123bar", r"\d+", "NUM", regex=True)
    assert result == "fooNUMbar"


def test_substitute_value_regex_invalid_raises():
    with pytest.raises(SubstitutionError):
        substitute_value("value", "[invalid", "x", regex=True)


def test_substitute_value_case_insensitive():
    result = substitute_value("Hello World", "hello", "Hi", case_sensitive=False)
    assert result == "Hi World"


def test_substitute_value_case_sensitive_no_match():
    result = substitute_value("Hello", "hello", "Hi", case_sensitive=True)
    assert result == "Hello"


# ---------------------------------------------------------------------------
# substitute_env
# ---------------------------------------------------------------------------

def test_substitute_env_replaces_all_values():
    env = {"A": "old_val", "B": "old_val", "C": "keep"}
    result = substitute_env(env, "old_val", "new_val")
    assert result["A"] == "new_val"
    assert result["B"] == "new_val"
    assert result["C"] == "keep"


def test_substitute_env_does_not_mutate_original():
    env = {"A": "old"}
    substitute_env(env, "old", "new")
    assert env["A"] == "old"


def test_substitute_env_keys_filter_limits_scope():
    env = {"A": "replace_me", "B": "replace_me"}
    result = substitute_env(env, "replace_me", "done", keys=["A"])
    assert result["A"] == "done"
    assert result["B"] == "replace_me"


def test_substitute_env_regex_mode():
    env = {"URL": "http://localhost:8080", "OTHER": "no-port"}
    result = substitute_env(env, r":\d+", ":9000", regex=True)
    assert result["URL"] == "http://localhost:9000"
    assert result["OTHER"] == "no-port"


def test_substitute_env_empty_env_returns_empty():
    assert substitute_env({}, "x", "y") == {}


# ---------------------------------------------------------------------------
# get_substituted_keys
# ---------------------------------------------------------------------------

def test_get_substituted_keys_detects_changes():
    original = {"A": "old", "B": "same"}
    updated = {"A": "new", "B": "same"}
    assert get_substituted_keys(original, updated) == ["A"]


def test_get_substituted_keys_no_changes_returns_empty():
    env = {"A": "val", "B": "val2"}
    assert get_substituted_keys(env, dict(env)) == []


def test_get_substituted_keys_multiple_changed():
    original = {"A": "1", "B": "2", "C": "3"}
    updated = {"A": "X", "B": "2", "C": "Y"}
    changed = get_substituted_keys(original, updated)
    assert set(changed) == {"A", "C"}
