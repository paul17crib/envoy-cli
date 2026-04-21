"""Tests for envoy/clamper.py"""

import pytest

from envoy.clamper import (
    ClamperError,
    clamp_value,
    clamp_env,
    get_clamped_keys,
)


# ---------------------------------------------------------------------------
# clamp_value
# ---------------------------------------------------------------------------

def test_clamp_value_within_range_unchanged():
    assert clamp_value("hello", min_len=3, max_len=10) == "hello"


def test_clamp_value_truncates_long_value():
    result = clamp_value("abcdefgh", min_len=0, max_len=5)
    assert result == "abcde"
    assert len(result) == 5


def test_clamp_value_truncates_with_suffix():
    result = clamp_value("abcdefgh", min_len=0, max_len=5, truncate_suffix="...")
    assert result == "ab..."
    assert len(result) == 5


def test_clamp_value_pads_short_value():
    result = clamp_value("hi", min_len=6, max_len=10)
    assert result == "hi    "
    assert len(result) == 6


def test_clamp_value_pads_with_custom_char():
    result = clamp_value("hi", min_len=5, max_len=10, pad_char="-")
    assert result == "hi---"


def test_clamp_value_empty_string_padded():
    result = clamp_value("", min_len=3, max_len=10)
    assert result == "   "


def test_clamp_value_exact_max_unchanged():
    assert clamp_value("exact", min_len=0, max_len=5) == "exact"


def test_clamp_value_invalid_range_raises():
    with pytest.raises(ClamperError, match="min_len"):
        clamp_value("x", min_len=10, max_len=5)


def test_clamp_value_negative_min_raises():
    with pytest.raises(ClamperError, match="min_len must be"):
        clamp_value("x", min_len=-1, max_len=5)


def test_clamp_value_bad_pad_char_raises():
    with pytest.raises(ClamperError, match="pad_char"):
        clamp_value("x", min_len=0, max_len=10, pad_char="--")


def test_clamp_value_suffix_too_long_raises():
    with pytest.raises(ClamperError, match="truncate_suffix"):
        clamp_value("hello", min_len=0, max_len=3, truncate_suffix="...")


# ---------------------------------------------------------------------------
# clamp_env
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_env():
    return {
        "SHORT": "hi",
        "LONG": "this_is_a_very_long_value_string",
        "NORMAL": "medium",
    }


def test_clamp_env_truncates_long_values(sample_env):
    result = clamp_env(sample_env, max_len=8)
    assert len(result["LONG"]) == 8
    assert result["SHORT"] == "hi"


def test_clamp_env_pads_short_values(sample_env):
    result = clamp_env(sample_env, min_len=5, max_len=50)
    assert len(result["SHORT"]) == 5


def test_clamp_env_does_not_mutate_original(sample_env):
    original_long = sample_env["LONG"]
    clamp_env(sample_env, max_len=5)
    assert sample_env["LONG"] == original_long


def test_clamp_env_keys_filter_restricts_changes(sample_env):
    result = clamp_env(sample_env, max_len=5, keys=["LONG"])
    assert len(result["LONG"]) == 5
    assert result["NORMAL"] == sample_env["NORMAL"]


def test_clamp_env_all_keys_processed_without_filter(sample_env):
    result = clamp_env(sample_env, min_len=4, max_len=10)
    for v in result.values():
        assert 4 <= len(v) <= 10


# ---------------------------------------------------------------------------
# get_clamped_keys
# ---------------------------------------------------------------------------

def test_get_clamped_keys_returns_changed(sample_env):
    clamped = clamp_env(sample_env, max_len=8)
    changed = get_clamped_keys(sample_env, clamped)
    assert "LONG" in changed
    assert "SHORT" not in changed


def test_get_clamped_keys_empty_when_nothing_changed(sample_env):
    clamped = clamp_env(sample_env, min_len=0, max_len=255)
    assert get_clamped_keys(sample_env, clamped) == []
