"""Tests for envoy.transformer."""

import pytest

from envoy.transformer import (
    TransformError,
    get_transform,
    get_transformed_keys,
    transform_env,
    transform_value,
)


def test_get_transform_upper():
    fn = get_transform("upper")
    assert fn("hello") == "HELLO"


def test_get_transform_lower():
    fn = get_transform("lower")
    assert fn("WORLD") == "world"


def test_get_transform_unknown_raises():
    with pytest.raises(TransformError, match="Unknown transform"):
        get_transform("nonexistent")


def test_transform_value_single_transform():
    assert transform_value("hello world", ["upper"]) == "HELLO WORLD"


def test_transform_value_chained_transforms():
    result = transform_value("  hello  ", ["strip", "upper"])
    assert result == "HELLO"


def test_transform_value_reverse():
    assert transform_value("abc", ["reverse"]) == "cba"


def test_transform_value_base64_roundtrip():
    original = "my-secret-value"
    encoded = transform_value(original, ["base64"])
    decoded = transform_value(encoded, ["unbase64"])
    assert decoded == original


def test_transform_value_empty_list_is_noop():
    assert transform_value("unchanged", []) == "unchanged"


def test_transform_env_applies_to_all_keys():
    env = {"APP_NAME": "myapp", "APP_ENV": "production"}
    result = transform_env(env, ["upper"])
    assert result == {"APP_NAME": "MYAPP", "APP_ENV": "PRODUCTION"}


def test_transform_env_does_not_mutate_original():
    env = {"KEY": "value"}
    transform_env(env, ["upper"])
    assert env["KEY"] == "value"


def test_transform_env_with_key_filter():
    env = {"A": "hello", "B": "world", "C": "foo"}
    result = transform_env(env, ["upper"], keys=["A", "C"])
    assert result["A"] == "HELLO"
    assert result["B"] == "world"
    assert result["C"] == "FOO"


def test_transform_env_missing_key_in_filter_is_ignored():
    env = {"A": "hello"}
    result = transform_env(env, ["upper"], keys=["A", "MISSING"])
    assert result["A"] == "HELLO"
    assert "MISSING" not in result


def test_get_transformed_keys_returns_changed():
    original = {"A": "hello", "B": "world"}
    transformed = {"A": "HELLO", "B": "world"}
    changed = get_transformed_keys(original, transformed)
    assert changed == ["A"]


def test_get_transformed_keys_empty_when_no_changes():
    env = {"A": "same"}
    assert get_transformed_keys(env, dict(env)) == []
