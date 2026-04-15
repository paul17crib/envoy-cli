"""Tests for envoy.differ2 (multi-file diff engine)."""

import pytest
from envoy.differ2 import multi_diff, MultiDiffEntry, MultiDiffReport


ENV_A = {"APP_NAME": "alpha", "DB_HOST": "localhost", "SECRET_KEY": "abc"}
ENV_B = {"APP_NAME": "alpha", "DB_HOST": "remotehost", "API_KEY": "xyz"}
ENV_C = {"APP_NAME": "alpha", "DB_HOST": "localhost", "SECRET_KEY": "abc", "NEW_KEY": "1"}


def test_report_contains_all_unique_keys():
    report = multi_diff({"a": ENV_A, "b": ENV_B})
    keys = {e.key for e in report.entries}
    assert keys == {"APP_NAME", "DB_HOST", "SECRET_KEY", "API_KEY"}


def test_consistent_key_detected():
    report = multi_diff({"a": ENV_A, "b": ENV_B})
    entry = next(e for e in report.entries if e.key == "APP_NAME")
    assert entry.is_consistent is True


def test_conflicting_key_detected():
    report = multi_diff({"a": ENV_A, "b": ENV_B})
    entry = next(e for e in report.entries if e.key == "DB_HOST")
    assert entry.has_value_conflict is True
    assert entry.is_consistent is False


def test_missing_key_detected():
    report = multi_diff({"a": ENV_A, "b": ENV_B})
    entry = next(e for e in report.entries if e.key == "SECRET_KEY")
    assert entry.is_missing_in_some is True
    assert entry.values["b"] is None


def test_report_consistent_keys_list():
    report = multi_diff({"a": ENV_A, "b": ENV_B})
    assert "APP_NAME" in report.consistent_keys
    assert "DB_HOST" not in report.consistent_keys


def test_report_conflicting_keys_list():
    report = multi_diff({"a": ENV_A, "b": ENV_B})
    assert "DB_HOST" in report.conflicting_keys


def test_report_missing_keys_list():
    report = multi_diff({"a": ENV_A, "b": ENV_B})
    assert "SECRET_KEY" in report.missing_keys
    assert "API_KEY" in report.missing_keys


def test_three_file_diff():
    report = multi_diff({"a": ENV_A, "b": ENV_B, "c": ENV_C})
    assert report.files == ["a", "b", "c"]
    keys = {e.key for e in report.entries}
    assert "NEW_KEY" in keys


def test_entries_sorted_by_key():
    report = multi_diff({"a": ENV_A, "b": ENV_B})
    key_list = [e.key for e in report.entries]
    assert key_list == sorted(key_list)


def test_empty_envs_produces_empty_report():
    report = multi_diff({"a": {}, "b": {}})
    assert report.entries == []


def test_identical_envs_all_consistent():
    report = multi_diff({"a": ENV_A, "b": ENV_A})
    assert report.conflicting_keys == []
    assert report.missing_keys == []
    assert set(report.consistent_keys) == set(ENV_A.keys())
