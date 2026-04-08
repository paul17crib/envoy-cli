"""Tests for envoy.sync module."""

import os
import pytest
from pathlib import Path

from envoy.sync import load_local, save_local, merge_envs, diff_envs, SyncError


@pytest.fixture
def tmp_env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("APP_NAME=envoy\nDEBUG=true\nSECRET_KEY=abc123\n")
    return str(p)


def test_load_local(tmp_env_file):
    env = load_local(tmp_env_file)
    assert env["APP_NAME"] == "envoy"
    assert env["DEBUG"] == "true"
    assert env["SECRET_KEY"] == "abc123"


def test_load_local_missing_file():
    with pytest.raises(FileNotFoundError):
        load_local("/nonexistent/.env")


def test_save_local(tmp_path):
    env = {"FOO": "bar", "BAZ": "qux"}
    out = str(tmp_path / "output.env")
    save_local(env, out)
    assert Path(out).exists()
    content = Path(out).read_text()
    assert "FOO=bar" in content
    assert "BAZ=qux" in content


def test_save_local_no_overwrite(tmp_env_file):
    with pytest.raises(SyncError):
        save_local({"X": "1"}, tmp_env_file, overwrite=False)


def test_save_local_overwrite(tmp_env_file):
    save_local({"ONLY": "this"}, tmp_env_file, overwrite=True)
    env = load_local(tmp_env_file)
    assert env == {"ONLY": "this"}


def test_merge_envs_override():
    base = {"A": "1", "B": "2"}
    override = {"B": "99", "C": "3"}
    result = merge_envs(base, override, strategy="override")
    assert result == {"A": "1", "B": "99", "C": "3"}


def test_merge_envs_keep():
    base = {"A": "1", "B": "2"}
    override = {"B": "99", "C": "3"}
    result = merge_envs(base, override, strategy="keep")
    assert result["B"] == "2"
    assert result["C"] == "3"
    assert result["A"] == "1"


def test_merge_envs_invalid_strategy():
    with pytest.raises(ValueError):
        merge_envs({}, {}, strategy="unknown")


def test_diff_envs():
    local = {"A": "1", "B": "old", "C": "same"}
    remote = {"B": "new", "C": "same", "D": "added"}
    diff = diff_envs(local, remote)
    assert "A" in diff["removed"]
    assert "D" in diff["added"]
    assert "B" in diff["changed"]
    assert diff["changed"]["B"] == {"local": "old", "remote": "new"}
    assert "C" in diff["unchanged"]
