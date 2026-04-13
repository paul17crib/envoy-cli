"""Tests for envoy.expander."""

from __future__ import annotations

import argparse
import pytest

from envoy.expander import (
    ExpansionError,
    expand_env,
    expand_value,
    get_expanded_keys,
)


# ---------------------------------------------------------------------------
# expand_value
# ---------------------------------------------------------------------------

def test_expand_value_brace_style():
    env = {"HOST": "localhost", "PORT": "5432"}
    assert expand_value("${HOST}:${PORT}", env) == "localhost:5432"


def test_expand_value_bare_style():
    env = {"NAME": "world"}
    assert expand_value("hello $NAME", env) == "hello world"


def test_expand_value_with_default_present():
    env = {"DB": "postgres"}
    assert expand_value("${DB:-sqlite}", env) == "postgres"


def test_expand_value_with_default_missing():
    assert expand_value("${MISSING:-fallback}", {}) == "fallback"


def test_expand_value_undefined_lenient():
    result = expand_value("${UNDEFINED}", {})
    assert result == "${UNDEFINED}"


def test_expand_value_undefined_strict_raises():
    with pytest.raises(ExpansionError, match="UNDEFINED"):
        expand_value("${UNDEFINED}", {}, strict=True)


def test_expand_value_no_references_unchanged():
    assert expand_value("plain-value", {}) == "plain-value"


def test_expand_value_empty_string():
    assert expand_value("", {"A": "1"}) == ""


# ---------------------------------------------------------------------------
# expand_env
# ---------------------------------------------------------------------------

def test_expand_env_resolves_chained_references():
    env = {"BASE": "/app", "LOG": "${BASE}/logs"}
    result = expand_env(env)
    assert result["LOG"] == "/app/logs"


def test_expand_env_does_not_mutate_original():
    env = {"A": "hello", "B": "$A world"}
    _ = expand_env(env)
    assert env["B"] == "$A world"


def test_expand_env_uses_extra_for_resolution():
    env = {"URL": "${SCHEME}://example.com"}
    result = expand_env(env, extra={"SCHEME": "https"})
    assert result["URL"] == "https://example.com"


def test_expand_env_extra_not_in_output():
    env = {"URL": "${SCHEME}://example.com"}
    result = expand_env(env, extra={"SCHEME": "https"})
    assert "SCHEME" not in result


def test_expand_env_strict_raises_on_missing():
    env = {"VAL": "${GHOST}"}
    with pytest.raises(ExpansionError):
        expand_env(env, strict=True)


def test_expand_env_returns_all_keys():
    env = {"A": "1", "B": "2", "C": "$A-$B"}
    result = expand_env(env)
    assert set(result.keys()) == {"A", "B", "C"}
    assert result["C"] == "1-2"


# ---------------------------------------------------------------------------
# get_expanded_keys
# ---------------------------------------------------------------------------

def test_get_expanded_keys_returns_changed():
    original = {"A": "$X", "B": "static"}
    expanded = {"A": "resolved", "B": "static"}
    assert get_expanded_keys(original, expanded) == ["A"]


def test_get_expanded_keys_empty_when_nothing_changed():
    env = {"A": "hello", "B": "world"}
    assert get_expanded_keys(env, dict(env)) == []
