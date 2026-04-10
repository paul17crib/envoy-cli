"""Tests for envoy.cli_snapshot."""

import argparse
import pytest
from io import StringIO

from envoy.cli_snapshot import run_snapshot, build_parser
from envoy.snapshotter import save_snapshot, load_snapshot
from envoy.sync import save_local


@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def env_file(temp_dir):
    path = temp_dir / ".env"
    path.write_text("APP_KEY=abc123\nDEBUG=true\n")
    return str(path)


def make_args(**kwargs):
    defaults = {"snapshot_cmd": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_save_snapshot_from_env_file(env_file, temp_dir):
    args = make_args(snapshot_cmd="save", name="v1", file=env_file, note="")
    out, err = StringIO(), StringIO()
    rc = run_snapshot(args, out=out, err=err)
    assert rc == 0
    assert "v1" in out.getvalue()


def test_save_snapshot_missing_file(temp_dir):
    args = make_args(snapshot_cmd="save", name="v1", file=str(temp_dir / "missing.env"), note="")
    out, err = StringIO(), StringIO()
    rc = run_snapshot(args, out=out, err=err)
    assert rc == 1
    assert "Error" in err.getvalue()


def test_restore_snapshot_writes_file(env_file, temp_dir):
    import os
    save_snapshot("snap1", {"RESTORED": "yes"}, base_dir=str(temp_dir))
    target = str(temp_dir / "restored.env")
    args = make_args(snapshot_cmd="restore", name="snap1", file=target, overwrite=False)
    out, err = StringIO(), StringIO()
    rc = run_snapshot(args, out=out, err=err)
    assert rc == 0
    env = load_snapshot("snap1", base_dir=str(temp_dir))
    assert env["RESTORED"] == "yes"


def test_restore_missing_snapshot(temp_dir):
    args = make_args(snapshot_cmd="restore", name="ghost", file=str(temp_dir / "out.env"), overwrite=False)
    out, err = StringIO(), StringIO()
    rc = run_snapshot(args, out=out, err=err)
    assert rc == 1
    assert "Error" in err.getvalue()


def test_list_no_snapshots(temp_dir, monkeypatch):
    monkeypatch.chdir(temp_dir)
    args = make_args(snapshot_cmd="list")
    out, err = StringIO(), StringIO()
    rc = run_snapshot(args, out=out, err=err)
    assert rc == 0
    assert "No snapshots" in out.getvalue()


def test_list_shows_saved_snapshots(temp_dir, monkeypatch):
    monkeypatch.chdir(temp_dir)
    save_snapshot("release", {"A": "1"}, base_dir=str(temp_dir))
    args = make_args(snapshot_cmd="list")
    out, err = StringIO(), StringIO()
    rc = run_snapshot(args, out=out, err=err)
    assert rc == 0
    assert "release" in out.getvalue()


def test_delete_existing_snapshot(temp_dir, monkeypatch):
    monkeypatch.chdir(temp_dir)
    save_snapshot("old", {"K": "v"}, base_dir=str(temp_dir))
    args = make_args(snapshot_cmd="delete", name="old")
    out, err = StringIO(), StringIO()
    rc = run_snapshot(args, out=out, err=err)
    assert rc == 0
    assert "deleted" in out.getvalue()


def test_delete_missing_snapshot(temp_dir, monkeypatch):
    monkeypatch.chdir(temp_dir)
    args = make_args(snapshot_cmd="delete", name="nope")
    out, err = StringIO(), StringIO()
    rc = run_snapshot(args, out=out, err=err)
    assert rc == 1


def test_no_subcommand_returns_error():
    args = make_args(snapshot_cmd=None)
    out, err = StringIO(), StringIO()
    rc = run_snapshot(args, out=out, err=err)
    assert rc == 1
