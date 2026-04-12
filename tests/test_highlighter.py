"""Tests for envoy.highlighter."""

import pytest
from envoy.highlighter import (
    highlight_text,
    highlight_env,
    filter_highlighted,
    count_matches,
    ANSI_YELLOW,
    ANSI_CYAN,
    ANSI_RESET,
)


SAMPLE_ENV = {
    "APP_NAME": "myapp",
    "DB_PASSWORD": "secret123",
    "DB_HOST": "localhost",
    "API_KEY": "abc-key-xyz",
    "DEBUG": "true",
}


def test_highlight_text_wraps_match():
    result = highlight_text("hello world", "world")
    assert f"{ANSI_YELLOW}world{ANSI_RESET}" in result


def test_highlight_text_case_insensitive_by_default():
    result = highlight_text("Hello World", "hello")
    assert f"{ANSI_YELLOW}Hello{ANSI_RESET}" in result


def test_highlight_text_case_sensitive_no_match():
    result = highlight_text("Hello World", "hello", case_sensitive=True)
    assert ANSI_YELLOW not in result
    assert result == "Hello World"


def test_highlight_text_custom_color():
    result = highlight_text("foo bar", "bar", color=ANSI_CYAN)
    assert f"{ANSI_CYAN}bar{ANSI_RESET}" in result


def test_highlight_text_no_match_returns_original():
    result = highlight_text("hello", "xyz")
    assert result == "hello"


def test_highlight_env_matches_key():
    entries = highlight_env(SAMPLE_ENV, "DB", search_keys=True, search_values=False)
    matched = [(k, v, m) for k, v, m in entries if m]
    assert len(matched) == 2  # DB_PASSWORD and DB_HOST


def test_highlight_env_matches_value():
    entries = highlight_env(SAMPLE_ENV, "localhost", search_keys=False, search_values=True)
    matched = [e for e in entries if e[2]]
    assert len(matched) == 1
    assert "localhost" in matched[0][1] or ANSI_YELLOW in matched[0][1]


def test_highlight_env_matches_both_key_and_value():
    env = {"SECRET": "secret_value"}
    entries = highlight_env(env, "secret")
    assert entries[0][2] is True


def test_highlight_env_no_match_returns_false():
    entries = highlight_env(SAMPLE_ENV, "NONEXISTENT")
    assert all(not matched for _, _, matched in entries)


def test_highlight_env_all_entries_returned():
    entries = highlight_env(SAMPLE_ENV, "DB")
    assert len(entries) == len(SAMPLE_ENV)


def test_filter_highlighted_only_matches():
    entries = highlight_env(SAMPLE_ENV, "DB")
    filtered = filter_highlighted(entries, only_matches=True)
    assert len(filtered) == 2
    assert all(isinstance(item, tuple) and len(item) == 2 for item in filtered)


def test_filter_highlighted_all_entries():
    entries = highlight_env(SAMPLE_ENV, "DB")
    all_entries = filter_highlighted(entries, only_matches=False)
    assert len(all_entries) == len(SAMPLE_ENV)


def test_count_matches_correct():
    entries = highlight_env(SAMPLE_ENV, "DB")
    assert count_matches(entries) == 2


def test_count_matches_zero_when_no_match():
    entries = highlight_env(SAMPLE_ENV, "ZZZNOMATCH")
    assert count_matches(entries) == 0


def test_highlight_env_case_sensitive():
    entries = highlight_env(SAMPLE_ENV, "db", case_sensitive=True)
    assert count_matches(entries) == 0


def test_highlight_env_empty_env():
    entries = highlight_env({}, "anything")
    assert entries == []
