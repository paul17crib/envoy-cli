"""Tests for envoy.normalizer module."""

import pytest
from envoy.normalizer import normalize_boolean, normalize_value, normalize_env, get_normalized_keys


def test_normalize_boolean_true_variants():
    for val in ["true", "True", "TRUE", "yes", "YES", "1", "on", "ON"]:
        assert normalize_boolean(val) == "true"


def test_normalize_boolean_false_variants():
    for val in ["false", "False", "FALSE", "no", "NO", "0", "off", "OFF"]:
        assert normalize_boolean(val) == "false"


def test_normalize_boolean_non_boolean_returns_none():
    assert normalize_boolean("hello") is None
    assert normalize_boolean("maybe") is None
    assert normalize_boolean("") is None


def test_normalize_value_strips_whitespace():
    assert normalize_value("  hello  ") == "hello"


def test_normalize_value_no_strip():
    assert normalize_value("  hello  ", strip_whitespace=False) == "  hello  "


def test_normalize_value_fixes_boolean():
    assert normalize_value("YES") == "true"
    assert normalize_value("NO") == "false"


def test_normalize_value_no_boolean_fix():
    assert normalize_value("YES", fix_booleans=False) == "YES"


def test_normalize_value_non_boolean_unchanged():
    assert normalize_value("my-secret-value") == "my-secret-value"


def test_normalize_env_normalizes_values():
    env = {"DEBUG": "True", "NAME": "  alice  ", "COUNT": "5"}
    result = normalize_env(env)
    assert result["DEBUG"] == "true"
    assert result["NAME"] == "alice"
    assert result["COUNT"] == "5"


def test_normalize_env_does_not_mutate_original():
    env = {"DEBUG": "True"}
    normalize_env(env)
    assert env["DEBUG"] == "True"


def test_normalize_env_uppercase_keys():
    env = {"debug": "true", "app_name": "envoy"}
    result = normalize_env(env, uppercase_keys=True)
    assert "DEBUG" in result
    assert "APP_NAME" in result
    assert "debug" not in result


def test_normalize_env_skip_booleans():
    env = {"FLAG": "yes"}
    result = normalize_env(env, fix_booleans=False)
    assert result["FLAG"] == "yes"


def test_get_normalized_keys_returns_changed_only():
    original = {"A": "True", "B": "hello", "C": "  world  "}
    normalized = {"A": "true", "B": "hello", "C": "world"}
    changed = get_normalized_keys(original, normalized)
    assert "A" in changed
    assert "C" in changed
    assert "B" not in changed


def test_get_normalized_keys_empty_when_no_changes():
    env = {"KEY": "value"}
    changed = get_normalized_keys(env, env.copy())
    assert changed == {}
