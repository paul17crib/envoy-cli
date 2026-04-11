"""Tests for envoy.grouper."""

import pytest
from envoy.grouper import (
    group_by_prefix,
    group_by_suffix,
    group_by_pattern,
    list_groups,
    get_group,
)


@pytest.fixture
def sample_env():
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "APP_NAME": "envoy",
        "APP_ENV": "production",
        "SECRET_KEY": "abc123",
        "NODELIMITER": "plain",
    }


def test_group_by_prefix_basic(sample_env):
    groups = group_by_prefix(sample_env)
    assert "DB" in groups
    assert "APP" in groups
    assert groups["DB"] == {"DB_HOST": "localhost", "DB_PORT": "5432"}


def test_group_by_prefix_no_delimiter_goes_to_ungrouped(sample_env):
    groups = group_by_prefix(sample_env)
    assert "__ungrouped__" in groups
    assert "NODELIMITER" in groups["__ungrouped__"]


def test_group_by_prefix_custom_delimiter():
    env = {"AWS-REGION": "us-east-1", "AWS-KEY": "key", "OTHER": "val"}
    groups = group_by_prefix(env, delimiter="-")
    assert "AWS" in groups
    assert groups["AWS"] == {"AWS-REGION": "us-east-1", "AWS-KEY": "key"}


def test_group_by_suffix_basic(sample_env):
    groups = group_by_suffix(sample_env)
    assert "HOST" in groups
    assert "PORT" in groups
    assert groups["HOST"] == {"DB_HOST": "localhost"}


def test_group_by_suffix_no_delimiter_goes_to_ungrouped(sample_env):
    groups = group_by_suffix(sample_env)
    assert "__ungrouped__" in groups
    assert "NODELIMITER" in groups["__ungrouped__"]


def test_group_by_pattern_matches_label():
    env = {"DB_HOST": "localhost", "APP_NAME": "envoy", "SECRET_KEY": "xyz"}
    patterns = ["database:^DB_", "app:^APP_"]
    groups = group_by_pattern(env, patterns)
    assert groups["database"] == {"DB_HOST": "localhost"}
    assert groups["app"] == {"APP_NAME": "envoy"}
    assert groups["__other__"] == {"SECRET_KEY": "xyz"}


def test_group_by_pattern_unmatched_goes_to_other():
    env = {"RANDOM_KEY": "val"}
    groups = group_by_pattern(env, ["db:^DB_"])
    assert "__other__" in groups
    assert groups["__other__"] == {"RANDOM_KEY": "val"}


def test_group_by_pattern_invalid_entry_raises():
    with pytest.raises(ValueError, match="label:regex"):
        group_by_pattern({"KEY": "val"}, ["no-colon-here"])


def test_group_by_pattern_first_match_wins():
    env = {"DB_SECRET": "s3cr3t"}
    patterns = ["database:^DB_", "secrets:SECRET"]
    groups = group_by_pattern(env, patterns)
    assert "DB_SECRET" in groups["database"]
    assert "secrets" not in groups


def test_list_groups_returns_sorted():
    groups = {"zebra": {}, "apple": {}, "mango": {}}
    assert list_groups(groups) == ["apple", "mango", "zebra"]


def test_get_group_existing(sample_env):
    groups = group_by_prefix(sample_env)
    result = get_group(groups, "DB")
    assert result is not None
    assert "DB_HOST" in result


def test_get_group_missing_returns_none(sample_env):
    groups = group_by_prefix(sample_env)
    assert get_group(groups, "NONEXISTENT") is None
