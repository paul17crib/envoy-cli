"""Tests for envoy/stringer.py"""

import pytest

from envoy.stringer import (
    StringerError,
    get_stringed_keys,
    pad_value,
    slugify_value,
    string_env,
    truncate_value,
    wrap_value,
)


# ---------------------------------------------------------------------------
# truncate_value
# ---------------------------------------------------------------------------

def test_truncate_short_value_unchanged():
    assert truncate_value("hello", 10) == "hello"


def test_truncate_exact_length_unchanged():
    assert truncate_value("hello", 5) == "hello"


def test_truncate_long_value_cut():
    result = truncate_value("hello world", 8)
    assert result == "hello..."
    assert len(result) == 8


def test_truncate_custom_suffix():
    assert truncate_value("hello world", 7, suffix="--") == "hello--"


def test_truncate_max_length_too_small_raises():
    with pytest.raises(StringerError):
        truncate_value("hi", 2, suffix="...")


# ---------------------------------------------------------------------------
# pad_value
# ---------------------------------------------------------------------------

def test_pad_left_default():
    assert pad_value("hi", 5) == "hi   "


def test_pad_right():
    assert pad_value("hi", 5, align="right") == "   hi"


def test_pad_center():
    result = pad_value("hi", 6, align="center")
    assert result == "  hi  "


def test_pad_custom_char():
    assert pad_value("hi", 5, char="-") == "hi---"


def test_pad_unknown_align_raises():
    with pytest.raises(StringerError, match="Unknown align"):
        pad_value("hi", 5, align="diagonal")


# ---------------------------------------------------------------------------
# slugify_value
# ---------------------------------------------------------------------------

def test_slugify_basic():
    assert slugify_value("Hello World") == "hello-world"


def test_slugify_special_chars_removed():
    assert slugify_value("foo@bar!") == "foobar"


def test_slugify_underscores_replaced():
    assert slugify_value("foo_bar_baz") == "foo-bar-baz"


def test_slugify_custom_separator():
    assert slugify_value("Hello World", separator="_") == "hello_world"


# ---------------------------------------------------------------------------
# wrap_value
# ---------------------------------------------------------------------------

def test_wrap_both_sides():
    assert wrap_value("value", prefix="[", suffix="]") == "[value]"


def test_wrap_prefix_only():
    assert wrap_value("value", prefix="${") == "${value"


def test_wrap_empty_strings():
    assert wrap_value("value") == "value"


# ---------------------------------------------------------------------------
# string_env
# ---------------------------------------------------------------------------

def test_string_env_truncate_all_keys():
    env = {"A": "hello world", "B": "short"}
    result = string_env(env, operation="truncate", max_length=8)
    assert result["A"] == "hello..."
    assert result["B"] == "short"


def test_string_env_restricts_to_keys():
    env = {"A": "hello world", "B": "hello world"}
    result = string_env(env, operation="truncate", keys=["A"], max_length=8)
    assert result["A"] == "hello..."
    assert result["B"] == "hello world"


def test_string_env_does_not_mutate_original():
    env = {"A": "hello world"}
    string_env(env, operation="truncate", max_length=8)
    assert env["A"] == "hello world"


def test_string_env_unknown_operation_raises():
    with pytest.raises(StringerError, match="Unknown operation"):
        string_env({"A": "v"}, operation="explode")


def test_string_env_slugify():
    env = {"LABEL": "My App Name", "OTHER": "unchanged"}
    result = string_env(env, operation="slugify", keys=["LABEL"])
    assert result["LABEL"] == "my-app-name"
    assert result["OTHER"] == "unchanged"


# ---------------------------------------------------------------------------
# get_stringed_keys
# ---------------------------------------------------------------------------

def test_get_stringed_keys_returns_changed():
    original = {"A": "hello world", "B": "ok"}
    updated = {"A": "hello...", "B": "ok"}
    assert get_stringed_keys(original, updated) == ["A"]


def test_get_stringed_keys_no_changes():
    env = {"A": "same", "B": "same"}
    assert get_stringed_keys(env, dict(env)) == []
