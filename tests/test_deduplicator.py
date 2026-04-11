"""Tests for envoy/deduplicator.py."""

import pytest
from envoy.deduplicator import (
    DuplicateEntry,
    find_duplicates,
    deduplicate_env,
    format_duplicate_report,
)


SAMPLE_LINES = [
    "APP_NAME=myapp\n",
    "DEBUG=true\n",
    "APP_NAME=otherapp\n",
    "SECRET_KEY=abc123\n",
    "DEBUG=false\n",
    "PORT=8080\n",
]

SAMPLE_ENV = {
    "APP_NAME": "otherapp",
    "DEBUG": "false",
    "SECRET_KEY": "abc123",
    "PORT": "8080",
}


def test_find_duplicates_detects_repeated_keys():
    result = find_duplicates(SAMPLE_LINES)
    assert "APP_NAME" in result
    assert "DEBUG" in result


def test_find_duplicates_returns_all_values():
    result = find_duplicates(SAMPLE_LINES)
    assert result["APP_NAME"] == ["myapp", "otherapp"]
    assert result["DEBUG"] == ["true", "false"]


def test_find_duplicates_ignores_unique_keys():
    result = find_duplicates(SAMPLE_LINES)
    assert "SECRET_KEY" not in result
    assert "PORT" not in result


def test_find_duplicates_ignores_comments_and_blanks():
    lines = ["# comment\n", "\n", "KEY=val\n", "KEY=val2\n"]
    result = find_duplicates(lines)
    assert "KEY" in result
    assert len(result["KEY"]) == 2


def test_find_duplicates_no_duplicates_returns_empty():
    lines = ["A=1\n", "B=2\n"]
    assert find_duplicates(lines) == {}


def test_deduplicate_env_last_strategy_keeps_last_value():
    deduped, entries = deduplicate_env(SAMPLE_ENV, SAMPLE_LINES, strategy="last")
    assert deduped["APP_NAME"] == "otherapp"
    assert deduped["DEBUG"] == "false"


def test_deduplicate_env_first_strategy_keeps_first_value():
    deduped, entries = deduplicate_env(SAMPLE_ENV, SAMPLE_LINES, strategy="first")
    assert deduped["APP_NAME"] == "myapp"
    assert deduped["DEBUG"] == "true"


def test_deduplicate_env_returns_duplicate_entries():
    _, entries = deduplicate_env(SAMPLE_ENV, SAMPLE_LINES)
    keys = [e.key for e in entries]
    assert "APP_NAME" in keys
    assert "DEBUG" in keys


def test_deduplicate_env_entry_occurrences_count():
    _, entries = deduplicate_env(SAMPLE_ENV, SAMPLE_LINES)
    entry = next(e for e in entries if e.key == "APP_NAME")
    assert entry.occurrences == 2


def test_deduplicate_env_preserves_non_duplicate_keys():
    deduped, _ = deduplicate_env(SAMPLE_ENV, SAMPLE_LINES)
    assert deduped["SECRET_KEY"] == "abc123"
    assert deduped["PORT"] == "8080"


def test_deduplicate_env_no_duplicates_returns_empty_entries():
    lines = ["A=1\n", "B=2\n"]
    env = {"A": "1", "B": "2"}
    deduped, entries = deduplicate_env(env, lines)
    assert entries == []
    assert deduped == env


def test_format_duplicate_report_with_entries():
    entries = [DuplicateEntry("APP_NAME", 2, "otherapp")]
    report = format_duplicate_report(entries)
    assert "APP_NAME" in report
    assert "2 occurrences" in report
    assert "otherapp" in report


def test_format_duplicate_report_no_entries():
    report = format_duplicate_report([])
    assert report == "No duplicate keys found."


def test_deduplicate_env_does_not_mutate_original():
    original = dict(SAMPLE_ENV)
    deduplicate_env(SAMPLE_ENV, SAMPLE_LINES)
    assert SAMPLE_ENV == original
