"""Tests for envoy/versioner.py"""

import pytest
from pathlib import Path

from envoy.versioner import (
    VersionError,
    delete_version,
    diff_version,
    list_versions,
    load_version,
    save_version,
)


@pytest.fixture
def base(tmp_path):
    return tmp_path


@pytest.fixture
def sample_env():
    return {"APP_HOST": "localhost", "APP_PORT": "8080", "SECRET_KEY": "abc123"}


def test_save_version_creates_file(base, sample_env):
    path = save_version(sample_env, "v1", base)
    assert path.exists()
    assert path.stem == "v1"


def test_save_version_duplicate_label_raises(base, sample_env):
    save_version(sample_env, "v1", base)
    with pytest.raises(VersionError, match="already exists"):
        save_version(sample_env, "v1", base)


def test_load_version_returns_env(base, sample_env):
    save_version(sample_env, "v1", base)
    loaded = load_version("v1", base)
    assert loaded == sample_env


def test_load_version_missing_label_raises(base):
    with pytest.raises(VersionError, match="not found"):
        load_version("nonexistent", base)


def test_list_versions_empty(base):
    assert list_versions(base) == []


def test_list_versions_returns_sorted_labels(base, sample_env):
    save_version(sample_env, "v2", base)
    save_version(sample_env, "v1", base)
    save_version(sample_env, "v3", base)
    assert list_versions(base) == ["v1", "v2", "v3"]


def test_delete_version_removes_file(base, sample_env):
    save_version(sample_env, "v1", base)
    delete_version("v1", base)
    assert list_versions(base) == []


def test_delete_version_missing_raises(base):
    with pytest.raises(VersionError, match="not found"):
        delete_version("ghost", base)


def test_diff_version_detects_changed_key(base, sample_env):
    save_version(sample_env, "v1", base)
    updated = {**sample_env, "APP_PORT": "9000"}
    changes = diff_version(updated, "v1", base)
    assert "APP_PORT" in changes
    assert changes["APP_PORT"] == "8080"


def test_diff_version_detects_added_key(base, sample_env):
    save_version(sample_env, "v1", base)
    updated = {**sample_env, "NEW_KEY": "new_value"}
    changes = diff_version(updated, "v1", base)
    assert "NEW_KEY" in changes
    assert changes["NEW_KEY"] is None


def test_diff_version_detects_removed_key(base, sample_env):
    save_version(sample_env, "v1", base)
    reduced = {k: v for k, v in sample_env.items() if k != "APP_HOST"}
    changes = diff_version(reduced, "v1", base)
    assert "APP_HOST" in changes
    assert changes["APP_HOST"] == "localhost"


def test_diff_version_no_changes_returns_empty(base, sample_env):
    save_version(sample_env, "v1", base)
    changes = diff_version(sample_env, "v1", base)
    assert changes == {}
