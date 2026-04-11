"""Tests for envoy.filterer."""

from __future__ import annotations

import pytest

from envoy.filterer import (
    exclude_keys,
    filter_by_key_pattern,
    filter_by_value_pattern,
    filter_empty,
    filter_non_empty,
    filter_non_sensitive,
    filter_sensitive,
)

SAMPLE: dict = {
    "APP_NAME": "myapp",
    "DATABASE_URL": "postgres://localhost/db",
    "SECRET_KEY": "s3cr3t",
    "API_TOKEN": "",
    "DEBUG": "true",
    "PASSWORD": "hunter2",
}


def test_filter_by_key_pattern_basic():
    result = filter_by_key_pattern(SAMPLE, r"^APP")
    assert "APP_NAME" in result
    assert "API_TOKEN" not in result


def test_filter_by_key_pattern_case_insensitive():
    result = filter_by_key_pattern(SAMPLE, r"secret", case_sensitive=False)
    assert "SECRET_KEY" in result


def test_filter_by_key_pattern_case_sensitive_no_match():
    result = filter_by_key_pattern(SAMPLE, r"secret", case_sensitive=True)
    assert result == {}


def test_filter_by_value_pattern_matches_substring():
    result = filter_by_value_pattern(SAMPLE, r"postgres")
    assert "DATABASE_URL" in result
    assert "APP_NAME" not in result


def test_filter_by_value_pattern_empty_value():
    result = filter_by_value_pattern(SAMPLE, r"^$")
    assert "API_TOKEN" in result
    assert "APP_NAME" not in result


def test_filter_sensitive_returns_only_sensitive_keys():
    result = filter_sensitive(SAMPLE)
    assert "SECRET_KEY" in result
    assert "PASSWORD" in result
    assert "API_TOKEN" in result
    assert "APP_NAME" not in result
    assert "DEBUG" not in result


def test_filter_non_sensitive_excludes_sensitive_keys():
    result = filter_non_sensitive(SAMPLE)
    assert "APP_NAME" in result
    assert "DEBUG" in result
    assert "SECRET_KEY" not in result
    assert "PASSWORD" not in result


def test_filter_empty_returns_blank_values_only():
    result = filter_empty(SAMPLE)
    assert result == {"API_TOKEN": ""}


def test_filter_non_empty_excludes_blank_values():
    result = filter_non_empty(SAMPLE)
    assert "API_TOKEN" not in result
    assert len(result) == len(SAMPLE) - 1


def test_exclude_keys_removes_listed_keys():
    result = exclude_keys(SAMPLE, ["DEBUG", "APP_NAME"])
    assert "DEBUG" not in result
    assert "APP_NAME" not in result
    assert "SECRET_KEY" in result


def test_exclude_keys_case_insensitive():
    result = exclude_keys(SAMPLE, ["debug"], case_sensitive=False)
    assert "DEBUG" not in result


def test_exclude_keys_case_sensitive_no_removal():
    result = exclude_keys(SAMPLE, ["debug"], case_sensitive=True)
    assert "DEBUG" in result


def test_filter_does_not_mutate_original():
    original = dict(SAMPLE)
    filter_sensitive(SAMPLE)
    assert SAMPLE == original
