"""Tests for envoy.truncator."""

import pytest
from envoy.truncator import (
    TruncateError,
    truncate_env,
    get_truncated_keys,
    pad_env,
)


@pytest.fixture
def sample_env() -> dict:
    return {
        "SHORT": "hi",
        "MEDIUM": "hello world",
        "LONG": "this is a rather long value that exceeds limits",
        "EMPTY": "",
    }


# --- truncate_env ---

def test_truncate_env_shortens_long_values(sample_env):
    result = truncate_env(sample_env, max_length=10)
    assert len(result["LONG"]) == 10
    assert result["LONG"].endswith("...")


def test_truncate_env_leaves_short_values_unchanged(sample_env):
    result = truncate_env(sample_env, max_length=20)
    assert result["SHORT"] == "hi"
    assert result["EMPTY"] == ""


def test_truncate_env_custom_suffix(sample_env):
    result = truncate_env(sample_env, max_length=8, suffix="--")
    assert result["LONG"].endswith("--")
    assert len(result["LONG"]) == 8


def test_truncate_env_does_not_mutate_original(sample_env):
    original_long = sample_env["LONG"]
    truncate_env(sample_env, max_length=10)
    assert sample_env["LONG"] == original_long


def test_truncate_env_restricts_to_keys(sample_env):
    result = truncate_env(sample_env, max_length=5, keys=["SHORT"])
    # LONG is not in keys, so it must be unchanged
    assert result["LONG"] == sample_env["LONG"]
    # SHORT fits within 5 chars already
    assert result["SHORT"] == "hi"


def test_truncate_env_raises_when_max_too_small(sample_env):
    with pytest.raises(TruncateError):
        truncate_env(sample_env, max_length=2, suffix="...")


def test_truncate_env_exact_length_unchanged(sample_env):
    value = "hello"
    env = {"KEY": value}
    result = truncate_env(env, max_length=5)
    assert result["KEY"] == value


# --- get_truncated_keys ---

def test_get_truncated_keys_returns_long_keys(sample_env):
    keys = get_truncated_keys(sample_env, max_length=10)
    assert "LONG" in keys
    assert "SHORT" not in keys


def test_get_truncated_keys_empty_when_all_fit(sample_env):
    keys = get_truncated_keys(sample_env, max_length=100)
    assert keys == []


def test_get_truncated_keys_respects_key_filter(sample_env):
    keys = get_truncated_keys(sample_env, max_length=5, keys=["SHORT"])
    assert keys == []


# --- pad_env ---

def test_pad_env_pads_short_values(sample_env):
    result = pad_env(sample_env, min_length=10)
    assert len(result["SHORT"]) == 10
    assert result["SHORT"].startswith("hi")


def test_pad_env_does_not_shorten_long_values(sample_env):
    original = sample_env["LONG"]
    result = pad_env(sample_env, min_length=5)
    assert result["LONG"] == original


def test_pad_env_right_align(sample_env):
    result = pad_env({"KEY": "hi"}, min_length=6, align="right")
    assert result["KEY"] == "    hi"


def test_pad_env_center_align():
    result = pad_env({"KEY": "ab"}, min_length=6, align="center")
    assert result["KEY"] == "  ab  "


def test_pad_env_custom_pad_char():
    result = pad_env({"KEY": "hi"}, min_length=5, pad_char="-")
    assert result["KEY"] == "hi---"


def test_pad_env_raises_on_multi_char_pad():
    with pytest.raises(TruncateError):
        pad_env({"KEY": "hi"}, min_length=5, pad_char="--")


def test_pad_env_raises_on_invalid_align():
    with pytest.raises(TruncateError):
        pad_env({"KEY": "hi"}, min_length=5, align="diagonal")


def test_pad_env_restricts_to_keys(sample_env):
    result = pad_env(sample_env, min_length=10, keys=["SHORT"])
    assert len(result["SHORT"]) == 10
    # MEDIUM was not in keys; must be unchanged
    assert result["MEDIUM"] == sample_env["MEDIUM"]
