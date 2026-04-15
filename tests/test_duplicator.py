"""Tests for envoy.duplicator."""

import pytest

from envoy.duplicator import (
    DuplicatorError,
    duplicate_key,
    duplicate_keys,
    get_duplicated_keys,
    preview_duplications,
)


@pytest.fixture
def sample_env():
    return {"DB_HOST": "localhost", "DB_PORT": "5432", "APP_NAME": "envoy"}


def test_duplicate_key_creates_copy(sample_env):
    result = duplicate_key(sample_env, "DB_HOST", "DATABASE_HOST")
    assert result["DATABASE_HOST"] == "localhost"


def test_duplicate_key_preserves_original(sample_env):
    result = duplicate_key(sample_env, "DB_HOST", "DATABASE_HOST")
    assert result["DB_HOST"] == "localhost"


def test_duplicate_key_does_not_mutate_original(sample_env):
    original_keys = set(sample_env.keys())
    duplicate_key(sample_env, "DB_HOST", "DATABASE_HOST")
    assert set(sample_env.keys()) == original_keys


def test_duplicate_key_missing_source_raises(sample_env):
    with pytest.raises(DuplicatorError, match="Source key"):
        duplicate_key(sample_env, "MISSING_KEY", "NEW_KEY")


def test_duplicate_key_existing_dest_raises_without_overwrite(sample_env):
    with pytest.raises(DuplicatorError, match="already exists"):
        duplicate_key(sample_env, "DB_HOST", "DB_PORT")


def test_duplicate_key_existing_dest_allowed_with_overwrite(sample_env):
    result = duplicate_key(sample_env, "DB_HOST", "DB_PORT", overwrite=True)
    assert result["DB_PORT"] == "localhost"


def test_duplicate_keys_multiple_pairs(sample_env):
    mapping = {"DB_HOST": "DATABASE_HOST", "APP_NAME": "SERVICE_NAME"}
    result = duplicate_keys(sample_env, mapping)
    assert result["DATABASE_HOST"] == "localhost"
    assert result["SERVICE_NAME"] == "envoy"


def test_duplicate_keys_preserves_all_originals(sample_env):
    mapping = {"DB_HOST": "DATABASE_HOST"}
    result = duplicate_keys(sample_env, mapping)
    for key in sample_env:
        assert key in result


def test_duplicate_keys_conflict_raises_without_overwrite(sample_env):
    with pytest.raises(DuplicatorError):
        duplicate_keys(sample_env, {"DB_HOST": "DB_PORT"})


def test_get_duplicated_keys_returns_new_keys(sample_env):
    updated = duplicate_key(sample_env, "DB_HOST", "DATABASE_HOST")
    new_keys = get_duplicated_keys(sample_env, updated)
    assert new_keys == ["DATABASE_HOST"]


def test_get_duplicated_keys_empty_when_no_change(sample_env):
    assert get_duplicated_keys(sample_env, dict(sample_env)) == []


def test_preview_duplications_shows_conflict(sample_env):
    preview = preview_duplications(sample_env, {"DB_HOST": "DB_PORT"})
    assert len(preview) == 1
    assert preview[0]["conflict"] is True


def test_preview_duplications_no_conflict(sample_env):
    preview = preview_duplications(sample_env, {"DB_HOST": "NEW_HOST"})
    assert preview[0]["conflict"] is False
    assert preview[0]["value"] == "localhost"


def test_preview_duplications_missing_source_shows_none_value(sample_env):
    preview = preview_duplications(sample_env, {"GHOST_KEY": "NEW_KEY"})
    assert preview[0]["value"] is None
