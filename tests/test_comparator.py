"""Tests for envoy.comparator."""

import pytest
from envoy.comparator import (
    ComparisonReport,
    compare_envs,
    format_comparison_report,
)


LEFT = {
    "APP_NAME": "myapp",
    "DEBUG": "true",
    "SECRET_KEY": "abc123",
    "DB_HOST": "localhost",
}

RIGHT = {
    "APP_NAME": "myapp",
    "DEBUG": "false",
    "SECRET_KEY": "xyz789",
    "PORT": "8080",
}


def test_compare_envs_shared_keys():
    report = compare_envs(LEFT, RIGHT)
    assert set(report.shared_keys) == {"APP_NAME", "DEBUG", "SECRET_KEY"}


def test_compare_envs_only_in_left():
    report = compare_envs(LEFT, RIGHT)
    assert report.only_in_left == ["DB_HOST"]


def test_compare_envs_only_in_right():
    report = compare_envs(LEFT, RIGHT)
    assert report.only_in_right == ["PORT"]


def test_compare_envs_matching_keys():
    report = compare_envs(LEFT, RIGHT)
    assert report.matching_keys == ["APP_NAME"]


def test_compare_envs_differing_keys():
    report = compare_envs(LEFT, RIGHT)
    assert set(report.differing_keys) == {"DEBUG", "SECRET_KEY"}


def test_similarity_score_identical():
    env = {"A": "1", "B": "2"}
    report = compare_envs(env, env)
    assert report.similarity_score == 1.0


def test_similarity_score_no_overlap():
    left = {"A": "1"}
    right = {"B": "2"}
    report = compare_envs(left, right)
    assert report.similarity_score == 0.0


def test_similarity_score_partial():
    left = {"A": "1", "B": "2"}
    right = {"A": "1", "C": "3"}
    report = compare_envs(left, right)
    # matching=1 (A), total unique=3 (A,B,C)
    assert report.similarity_score == pytest.approx(1 / 3, rel=1e-3)


def test_total_unique_keys():
    report = compare_envs(LEFT, RIGHT)
    # LEFT has 4, RIGHT has 4, overlap 3 => total unique = 5
    assert report.total_unique_keys == 5


def test_empty_envs_score_is_one():
    report = compare_envs({}, {})
    assert report.similarity_score == 1.0


def test_format_report_contains_score():
    report = compare_envs(LEFT, RIGHT)
    text = format_comparison_report(report, left_label="local", right_label="remote")
    assert "Similarity score" in text
    assert "Only in local" in text
    assert "Only in remote" in text


def test_format_report_no_exclusive_keys_omits_lines():
    env = {"A": "1", "B": "2"}
    report = compare_envs(env, env)
    text = format_comparison_report(report)
    assert "Only in" not in text


def test_compare_envs_sorted_lists():
    left = {"Z": "1", "A": "2", "M": "3"}
    right = {"Z": "1", "A": "2", "M": "3"}
    report = compare_envs(left, right)
    assert report.shared_keys == sorted(left.keys())
    assert report.matching_keys == sorted(left.keys())
