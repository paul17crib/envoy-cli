"""Tests for envoy.renamer."""

import pytest

from envoy.renamer import (
    RenameError,
    RenameResult,
    bulk_rename,
    format_rename_report,
    rename_key,
)


@pytest.fixture
def sample_env():
    return {
        "APP_NAME": "myapp",
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "SECRET_KEY": "abc123",
    }


# --- rename_key ---

def test_rename_key_renames_successfully(sample_env):
    result = rename_key(sample_env, "APP_NAME", "APPLICATION_NAME")
    assert "APPLICATION_NAME" in result
    assert "APP_NAME" not in result
    assert result["APPLICATION_NAME"] == "myapp"


def test_rename_key_preserves_other_keys(sample_env):
    result = rename_key(sample_env, "DB_HOST", "DATABASE_HOST")
    assert result["DB_PORT"] == "5432"
    assert result["SECRET_KEY"] == "abc123"


def test_rename_key_missing_old_key_raises(sample_env):
    with pytest.raises(RenameError, match="not found"):
        rename_key(sample_env, "NONEXISTENT", "NEW_KEY")


def test_rename_key_existing_new_key_raises_without_overwrite(sample_env):
    with pytest.raises(RenameError, match="already exists"):
        rename_key(sample_env, "APP_NAME", "DB_HOST")


def test_rename_key_existing_new_key_allowed_with_overwrite(sample_env):
    result = rename_key(sample_env, "APP_NAME", "DB_HOST", overwrite=True)
    assert result["DB_HOST"] == "myapp"
    assert "APP_NAME" not in result


def test_rename_key_does_not_mutate_original(sample_env):
    original_keys = set(sample_env.keys())
    rename_key(sample_env, "APP_NAME", "APPLICATION_NAME")
    assert set(sample_env.keys()) == original_keys


# --- bulk_rename ---

def test_bulk_rename_applies_multiple_renames(sample_env):
    mapping = {"APP_NAME": "APPLICATION_NAME", "DB_HOST": "DATABASE_HOST"}
    new_env, result = bulk_rename(sample_env, mapping)
    assert "APPLICATION_NAME" in new_env
    assert "DATABASE_HOST" in new_env
    assert "APP_NAME" not in new_env
    assert "DB_HOST" not in new_env
    assert result.total_renamed == 2
    assert result.total_skipped == 0


def test_bulk_rename_skip_missing_records_skipped(sample_env):
    mapping = {"MISSING_KEY": "NEW_KEY", "APP_NAME": "APPLICATION_NAME"}
    new_env, result = bulk_rename(sample_env, mapping, skip_missing=True)
    assert result.total_skipped == 1
    assert result.total_renamed == 1
    assert new_env["APPLICATION_NAME"] == "myapp"


def test_bulk_rename_missing_key_raises_without_skip(sample_env):
    with pytest.raises(RenameError, match="not found"):
        bulk_rename(sample_env, {"MISSING": "OTHER"})


def test_bulk_rename_conflict_skipped_without_overwrite(sample_env):
    mapping = {"APP_NAME": "DB_HOST"}
    new_env, result = bulk_rename(sample_env, mapping, overwrite=False)
    assert result.total_skipped == 1
    assert new_env["APP_NAME"] == "myapp"  # unchanged


def test_bulk_rename_empty_mapping_returns_copy(sample_env):
    new_env, result = bulk_rename(sample_env, {})
    assert new_env == sample_env
    assert result.total_renamed == 0


# --- format_rename_report ---

def test_format_rename_report_shows_renames():
    result = RenameResult()
    result.renamed.append(("OLD", "NEW"))
    report = format_rename_report(result)
    assert "renamed: OLD -> NEW" in report


def test_format_rename_report_shows_skipped():
    result = RenameResult()
    result.skipped.append(("MISSING", "key not found"))
    report = format_rename_report(result)
    assert "skipped: MISSING" in report


def test_format_rename_report_no_changes():
    result = RenameResult()
    report = format_rename_report(result)
    assert "no changes made" in report
