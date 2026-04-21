"""Tests for envoy.swapper."""

from __future__ import annotations

import argparse

import pytest

from envoy.swapper import (
    SwapError,
    get_swap_preview,
    swap_keys,
    swap_names,
    swap_with_default,
)


@pytest.fixture
def sample_env():
    return {"FOO": "foo_val", "BAR": "bar_val", "BAZ": "baz_val"}


# --- swap_keys ---

def test_swap_keys_exchanges_values(sample_env):
    result = swap_keys(sample_env, "FOO", "BAR")
    assert result["FOO"] == "bar_val"
    assert result["BAR"] == "foo_val"


def test_swap_keys_preserves_other_keys(sample_env):
    result = swap_keys(sample_env, "FOO", "BAR")
    assert result["BAZ"] == "baz_val"


def test_swap_keys_does_not_mutate_original(sample_env):
    swap_keys(sample_env, "FOO", "BAR")
    assert sample_env["FOO"] == "foo_val"
    assert sample_env["BAR"] == "bar_val"


def test_swap_keys_missing_key_a_raises(sample_env):
    with pytest.raises(SwapError, match="MISSING"):
        swap_keys(sample_env, "MISSING", "BAR")


def test_swap_keys_missing_key_b_raises(sample_env):
    with pytest.raises(SwapError, match="MISSING"):
        swap_keys(sample_env, "FOO", "MISSING")


# --- swap_names ---

def test_swap_names_renames_keys(sample_env):
    result = swap_names(sample_env, "FOO", "BAR")
    assert "FOO" in result
    assert "BAR" in result
    assert result["FOO"] == "bar_val"
    assert result["BAR"] == "foo_val"


def test_swap_names_preserves_other_keys(sample_env):
    result = swap_names(sample_env, "FOO", "BAR")
    assert result["BAZ"] == "baz_val"


def test_swap_names_does_not_mutate_original(sample_env):
    swap_names(sample_env, "FOO", "BAR")
    assert sample_env["FOO"] == "foo_val"


def test_swap_names_missing_key_raises(sample_env):
    with pytest.raises(SwapError):
        swap_names(sample_env, "NOPE", "BAR")


# --- swap_with_default ---

def test_swap_with_default_both_present(sample_env):
    result = swap_with_default(sample_env, "FOO", "BAR")
    assert result["FOO"] == "bar_val"
    assert result["BAR"] == "foo_val"


def test_swap_with_default_missing_key_uses_default(sample_env):
    result = swap_with_default(sample_env, "FOO", "NEW_KEY", default="default_val")
    assert result["FOO"] == "default_val"
    assert result["NEW_KEY"] == "foo_val"


def test_swap_with_default_empty_default(sample_env):
    result = swap_with_default(sample_env, "FOO", "GHOST")
    assert result["FOO"] == ""
    assert result["GHOST"] == "foo_val"


# --- get_swap_preview ---

def test_get_swap_preview_shows_before_and_after(sample_env):
    preview = get_swap_preview(sample_env, "FOO", "BAR")
    assert preview["FOO"]["before"] == "foo_val"
    assert preview["FOO"]["after"] == "bar_val"
    assert preview["BAR"]["before"] == "bar_val"
    assert preview["BAR"]["after"] == "foo_val"


def test_get_swap_preview_missing_key_shows_empty(sample_env):
    preview = get_swap_preview(sample_env, "FOO", "MISSING")
    assert preview["MISSING"]["before"] == ""
    assert preview["FOO"]["after"] == ""
