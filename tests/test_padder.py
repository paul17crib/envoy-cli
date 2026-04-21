"""Tests for envoy.padder."""

import pytest

from envoy.padder import (
    PadderError,
    _max_key_length,
    _max_value_length,
    get_padded_keys,
    pad_keys,
    pad_values,
)


@pytest.fixture
def sample_env():
    return {
        "DB": "localhost",
        "DB_PORT": "5432",
        "APP_NAME": "envoy",
        "SECRET": "abc",
    }


def test_max_key_length_all_keys(sample_env):
    assert _max_key_length(sample_env) == len("APP_NAME")


def test_max_key_length_subset(sample_env):
    assert _max_key_length(sample_env, ["DB", "SECRET"]) == len("SECRET")


def test_max_key_length_empty_returns_zero():
    assert _max_key_length({}) == 0


def test_max_value_length_all_keys(sample_env):
    assert _max_value_length(sample_env) == len("localhost")


def test_max_value_length_subset(sample_env):
    assert _max_value_length(sample_env, ["DB_PORT", "SECRET"]) == len("DB_PORT")


def test_pad_values_left_align_auto_width(sample_env):
    padded = pad_values(sample_env)
    max_len = _max_value_length(sample_env)
    for v in padded.values():
        assert len(v) == max_len


def test_pad_values_right_align(sample_env):
    padded = pad_values(sample_env, align="right")
    max_len = _max_value_length(sample_env)
    for v in padded.values():
        assert len(v) == max_len
        # right-aligned: original value is at the end
    assert padded["SECRET"].endswith("abc")


def test_pad_values_explicit_width(sample_env):
    padded = pad_values(sample_env, width=20)
    for v in padded.values():
        assert len(v) == 20


def test_pad_values_does_not_mutate_original(sample_env):
    original_copy = dict(sample_env)
    pad_values(sample_env)
    assert sample_env == original_copy


def test_pad_values_subset_of_keys(sample_env):
    padded = pad_values(sample_env, keys=["DB", "SECRET"])
    assert len(padded["DB"]) == len(padded["SECRET"])
    # untouched key keeps original value
    assert padded["APP_NAME"] == sample_env["APP_NAME"]


def test_pad_values_invalid_fill_raises(sample_env):
    with pytest.raises(PadderError, match="fill must be exactly one character"):
        pad_values(sample_env, fill="XX")


def test_pad_values_invalid_align_raises(sample_env):
    with pytest.raises(PadderError, match="align must be"):
        pad_values(sample_env, align="center")


def test_pad_keys_auto_width(sample_env):
    padded = pad_keys(sample_env)
    max_len = _max_key_length(sample_env)
    for k in padded:
        assert len(k) == max_len


def test_pad_keys_explicit_width(sample_env):
    padded = pad_keys(sample_env, width=15)
    for k in padded:
        assert len(k) == 15


def test_pad_keys_invalid_fill_raises(sample_env):
    with pytest.raises(PadderError):
        pad_keys(sample_env, fill="--")


def test_get_padded_keys_detects_changed_values(sample_env):
    padded = pad_values(sample_env, width=20)
    changed = get_padded_keys(sample_env, padded)
    # all values are shorter than 20, so all should be changed
    assert set(changed) == set(sample_env.keys())


def test_get_padded_keys_no_change_when_already_padded():
    env = {"A": "hello"}
    padded = pad_values(env, width=5)
    assert get_padded_keys(env, padded) == []
