"""Tests for envoy.counter."""

import pytest
from envoy.counter import (
    CounterError,
    CountResult,
    count_env,
    count_in_value,
    get_matching_keys,
    total_matches,
)


def test_count_in_value_simple_match():
    matches = count_in_value("hello world hello", "hello")
    assert matches == ["hello", "hello"]


def test_count_in_value_case_insensitive_default():
    matches = count_in_value("Hello HELLO hello", "hello")
    assert len(matches) == 3


def test_count_in_value_case_sensitive_no_match():
    matches = count_in_value("HELLO", "hello", case_sensitive=True)
    assert matches == []


def test_count_in_value_regex():
    matches = count_in_value("abc123def456", r"\d+", regex=True)
    assert matches == ["123", "456"]


def test_count_in_value_empty_pattern_raises():
    with pytest.raises(CounterError, match="empty"):
        count_in_value("value", "")


def test_count_in_value_invalid_regex_raises():
    with pytest.raises(CounterError, match="Invalid regex"):
        count_in_value("value", "[", regex=True)


def test_count_env_counts_across_values():
    env = {"A": "foo bar foo", "B": "bar", "C": "no match"}
    results = count_env(env, "foo")
    by_key = {r.key: r.count for r in results}
    assert by_key["A"] == 2
    assert by_key["B"] == 0
    assert by_key["C"] == 0


def test_count_env_restricts_to_keys():
    env = {"A": "foo", "B": "foo", "C": "foo"}
    results = count_env(env, "foo", keys=["A", "C"])
    result_keys = [r.key for r in results]
    assert "B" not in result_keys
    assert "A" in result_keys
    assert "C" in result_keys


def test_count_env_include_keys_searches_key_name():
    env = {"APP_NAME": "myapp", "DB_HOST": "localhost"}
    results = count_env(env, "APP", include_keys=True)
    by_key = {r.key: r.count for r in results}
    assert by_key["APP_NAME"] >= 1


def test_total_matches_sums_counts():
    results = [
        CountResult(key="A", value="x", count=3),
        CountResult(key="B", value="y", count=1),
        CountResult(key="C", value="z", count=0),
    ]
    assert total_matches(results) == 4


def test_get_matching_keys_filters_zero_counts():
    results = [
        CountResult(key="A", value="x", count=2),
        CountResult(key="B", value="y", count=0),
    ]
    assert get_matching_keys(results) == ["A"]


def test_count_result_repr():
    r = CountResult(key="FOO", value="bar", count=5)
    assert "FOO" in repr(r)
    assert "5" in repr(r)
