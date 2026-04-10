"""Unit tests for envoy.snapshotter."""

import pytest
from envoy.snapshotter import (
    save_snapshot,
    load_snapshot,
    list_snapshots,
    delete_snapshot,
    snapshot_dir,
)


@pytest.fixture
def base(tmp_path):
    return str(tmp_path)


def test_save_snapshot_creates_file(base):
    env = {"KEY": "value", "PORT": "8080"}
    path = save_snapshot("test", env, base_dir=base)
    assert path.exists()


def test_load_snapshot_returns_env(base):
    env = {"DB_HOST": "localhost", "DB_PORT": "5432"}
    save_snapshot("db", env, base_dir=base)
    loaded = load_snapshot("db", base_dir=base)
    assert loaded == env


def test_load_snapshot_missing_raises(base):
    with pytest.raises(FileNotFoundError, match="Snapshot 'ghost' not found"):
        load_snapshot("ghost", base_dir=base)


def test_save_snapshot_stores_note(base):
    import json
    from envoy.snapshotter import _snapshot_path
    save_snapshot("noted", {"A": "1"}, base_dir=base, note="before deploy")
    payload = json.loads(_snapshot_path("noted", base).read_text())
    assert payload["note"] == "before deploy"


def test_list_snapshots_empty(base):
    assert list_snapshots(base_dir=base) == []


def test_list_snapshots_returns_metadata(base):
    save_snapshot("alpha", {"A": "1"}, base_dir=base)
    save_snapshot("beta", {"B": "2", "C": "3"}, base_dir=base)
    snapshots = list_snapshots(base_dir=base)
    names = [s["name"] for s in snapshots]
    assert "alpha" in names
    assert "beta" in names


def test_list_snapshots_key_count(base):
    save_snapshot("counted", {"X": "1", "Y": "2", "Z": "3"}, base_dir=base)
    snapshots = list_snapshots(base_dir=base)
    entry = next(s for s in snapshots if s["name"] == "counted")
    assert entry["key_count"] == 3


def test_delete_snapshot_removes_file(base):
    save_snapshot("temp", {"T": "1"}, base_dir=base)
    result = delete_snapshot("temp", base_dir=base)
    assert result is True
    with pytest.raises(FileNotFoundError):
        load_snapshot("temp", base_dir=base)


def test_delete_snapshot_missing_returns_false(base):
    assert delete_snapshot("nonexistent", base_dir=base) is False


def test_snapshot_dir_is_inside_base(base):
    sdir = snapshot_dir(base_dir=base)
    assert str(sdir).startswith(base)
