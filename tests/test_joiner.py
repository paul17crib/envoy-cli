"""Tests for envoy.joiner."""

import pytest

from envoy.joiner import JoinerError, join_keys, split_key, get_joined_keys


@pytest.fixture
def sample_env():
    return {
        "FIRST_NAME": "Ada",
        "LAST_NAME": "Lovelace",
        "CITY": "London",
        "COUNTRY": "UK",
    }


def test_join_keys_basic(sample_env):
    result = join_keys(sample_env, ["FIRST_NAME", "LAST_NAME"], "FULL_NAME")
    assert result["FULL_NAME"] == "Ada Lovelace"


def test_join_keys_custom_separator(sample_env):
    result = join_keys(sample_env, ["CITY", "COUNTRY"], "LOCATION", separator=", ")
    assert result["LOCATION"] == "London, UK"


def test_join_keys_does_not_mutate_original(sample_env):
    original_copy = dict(sample_env)
    join_keys(sample_env, ["FIRST_NAME", "LAST_NAME"], "FULL_NAME")
    assert sample_env == original_copy


def test_join_keys_preserves_existing_keys(sample_env):
    result = join_keys(sample_env, ["FIRST_NAME", "LAST_NAME"], "FULL_NAME")
    assert result["CITY"] == "London"
    assert result["COUNTRY"] == "UK"


def test_join_keys_missing_key_raises(sample_env):
    with pytest.raises(JoinerError, match="MISSING"):
        join_keys(sample_env, ["FIRST_NAME", "MISSING"], "FULL_NAME")


def test_join_keys_missing_ok_skips(sample_env):
    result = join_keys(sample_env, ["FIRST_NAME", "MISSING"], "FULL_NAME", missing_ok=True)
    assert result["FULL_NAME"] == "Ada"


def test_join_keys_no_overwrite_raises_when_dest_exists(sample_env):
    env = {**sample_env, "FULL_NAME": "existing"}
    with pytest.raises(JoinerError, match="overwrite=False"):
        join_keys(env, ["FIRST_NAME", "LAST_NAME"], "FULL_NAME", overwrite=False)


def test_join_keys_overwrite_replaces_existing(sample_env):
    env = {**sample_env, "FULL_NAME": "old value"}
    result = join_keys(env, ["FIRST_NAME", "LAST_NAME"], "FULL_NAME", overwrite=True)
    assert result["FULL_NAME"] == "Ada Lovelace"


def test_join_keys_empty_keys_raises(sample_env):
    with pytest.raises(JoinerError, match="At least one source key"):
        join_keys(sample_env, [], "DEST")


def test_join_keys_empty_dest_raises(sample_env):
    with pytest.raises(JoinerError, match="Destination key must not be empty"):
        join_keys(sample_env, ["FIRST_NAME"], "")


def test_split_key_basic(sample_env):
    env = {**sample_env, "FULL_NAME": "Ada Lovelace"}
    result = split_key(env, "FULL_NAME", ["FIRST", "LAST"])
    assert result["FIRST"] == "Ada"
    assert result["LAST"] == "Lovelace"


def test_split_key_custom_separator():
    env = {"COORDS": "51.5,-0.1"}
    result = split_key(env, "COORDS", ["LAT", "LNG"], separator=",")
    assert result["LAT"] == "51.5"
    assert result["LNG"] == "-0.1"


def test_split_key_segment_count_mismatch_raises():
    env = {"FULL": "one two three"}
    with pytest.raises(JoinerError, match="Expected 2 segments"):
        split_key(env, "FULL", ["A", "B"])


def test_split_key_missing_source_raises():
    with pytest.raises(JoinerError, match="MISSING"):
        split_key({}, "MISSING", ["A"])


def test_split_key_no_overwrite_raises():
    env = {"FULL": "Ada Lovelace", "FIRST": "existing"}
    with pytest.raises(JoinerError, match="overwrite=False"):
        split_key(env, "FULL", ["FIRST", "LAST"], overwrite=False)


def test_get_joined_keys_detects_new_key():
    original = {"A": "1"}
    updated = {"A": "1", "B": "2"}
    assert get_joined_keys(original, updated) == ["B"]


def test_get_joined_keys_detects_changed_key():
    original = {"A": "old"}
    updated = {"A": "new"}
    assert get_joined_keys(original, updated) == ["A"]


def test_get_joined_keys_no_changes():
    env = {"A": "1", "B": "2"}
    assert get_joined_keys(env, dict(env)) == []
