"""Tests for envoy.splitter."""

import pytest
from envoy.splitter import (
    SplitError,
    split_by_prefix,
    split_by_pattern,
    list_split_keys,
    get_split_bucket,
)


@pytest.fixture()
def sample_env():
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "APP_NAME": "envoy",
        "APP_DEBUG": "true",
        "SECRET_KEY": "abc123",
        "PORT": "8080",
    }


# --- split_by_prefix ---

def test_split_by_prefix_groups_correctly(sample_env):
    groups = split_by_prefix(sample_env)
    assert "DB" in groups
    assert "APP" in groups
    assert set(groups["DB"].keys()) == {"DB_HOST", "DB_PORT"}


def test_split_by_prefix_ungrouped_keys(sample_env):
    groups = split_by_prefix(sample_env)
    # PORT has no underscore
    assert "PORT" in groups["__ungrouped__"]


def test_split_by_prefix_strip_prefix(sample_env):
    groups = split_by_prefix(sample_env, strip_prefix=True)
    assert "HOST" in groups["DB"]
    assert "PORT" in groups["DB"]
    assert "NAME" in groups["APP"]


def test_split_by_prefix_custom_delimiter():
    env = {"DB.HOST": "localhost", "DB.PORT": "5432", "PLAIN": "yes"}
    groups = split_by_prefix(env, delimiter=".")
    assert "DB" in groups
    assert "PLAIN" in groups["__ungrouped__"]


def test_split_by_prefix_empty_env():
    groups = split_by_prefix({})
    assert groups == {}


def test_split_by_prefix_preserves_values(sample_env):
    groups = split_by_prefix(sample_env)
    assert groups["DB"]["DB_HOST"] == "localhost"
    assert groups["APP"]["APP_DEBUG"] == "true"


# --- split_by_pattern ---

def test_split_by_pattern_assigns_to_correct_bucket(sample_env):
    patterns = {"database": r"^DB_", "app": r"^APP_"}
    groups = split_by_pattern(sample_env, patterns)
    assert "DB_HOST" in groups["database"]
    assert "APP_NAME" in groups["app"]


def test_split_by_pattern_unmatched_goes_to_default(sample_env):
    patterns = {"database": r"^DB_"}
    groups = split_by_pattern(sample_env, patterns)
    assert "SECRET_KEY" in groups["__other__"]
    assert "PORT" in groups["__other__"]


def test_split_by_pattern_custom_default_bucket(sample_env):
    patterns = {"database": r"^DB_"}
    groups = split_by_pattern(sample_env, patterns, default_bucket="misc")
    assert "misc" in groups
    assert "__other__" not in groups


def test_split_by_pattern_first_match_wins():
    env = {"DB_SECRET": "s3cr3t"}
    patterns = {"database": r"^DB_", "secrets": r"SECRET"}
    groups = split_by_pattern(env, patterns)
    assert "DB_SECRET" in groups["database"]
    assert "secrets" not in groups


# --- list_split_keys ---

def test_list_split_keys_returns_sorted_keys(sample_env):
    groups = split_by_prefix(sample_env)
    key_map = list_split_keys(groups)
    assert key_map["DB"] == sorted(["DB_HOST", "DB_PORT"])


# --- get_split_bucket ---

def test_get_split_bucket_existing(sample_env):
    groups = split_by_prefix(sample_env)
    bucket = get_split_bucket(groups, "DB")
    assert bucket is not None
    assert "DB_HOST" in bucket


def test_get_split_bucket_missing(sample_env):
    groups = split_by_prefix(sample_env)
    assert get_split_bucket(groups, "NONEXISTENT") is None
