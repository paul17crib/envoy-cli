"""Unit tests for envoy.walker."""

from __future__ import annotations

import pytest
from pathlib import Path

from envoy.walker import (
    WalkerError,
    _is_env_file,
    collect_env_files,
    summarize_walk,
    walk_env_files,
)


@pytest.fixture()
def env_tree(tmp_path: Path) -> Path:
    """Create a small directory tree with .env files."""
    (tmp_path / ".env").write_text("A=1\n")
    (tmp_path / "README.md").write_text("# readme\n")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / ".env.local").write_text("B=2\n")
    (sub / ".env.example").write_text("B=\n")
    deep = sub / "deep"
    deep.mkdir()
    (deep / ".env").write_text("C=3\n")
    hidden = tmp_path / ".hidden"
    hidden.mkdir()
    (hidden / ".env").write_text("SECRET=x\n")
    return tmp_path


def test_is_env_file_matches_dotenv():
    assert _is_env_file(Path(".env"), [".env"]) is True


def test_is_env_file_matches_suffix():
    assert _is_env_file(Path(".env.local"), [".env.local"]) is True


def test_is_env_file_no_match():
    assert _is_env_file(Path("config.yaml"), [".env"]) is False


def test_collect_env_files_finds_expected(env_tree: Path):
    files = collect_env_files(env_tree)
    names = {f.name for f in files}
    assert ".env" in names
    assert ".env.local" in names
    assert ".env.example" in names


def test_collect_env_files_skips_hidden_by_default(env_tree: Path):
    files = collect_env_files(env_tree, skip_hidden=True)
    parents = {f.parent.name for f in files}
    assert ".hidden" not in parents


def test_collect_env_files_includes_hidden_when_requested(env_tree: Path):
    files = collect_env_files(env_tree, skip_hidden=False)
    parents = {f.parent.name for f in files}
    assert ".hidden" in parents


def test_collect_env_files_respects_max_depth(env_tree: Path):
    # depth 0 = root only; sub is depth 1, deep is depth 2
    files = collect_env_files(env_tree, max_depth=1)
    names = [f.name for f in files]
    # root .env and sub/.env.local, sub/.env.example should be found
    assert ".env" in names
    # deep/.env is at depth 2 — should NOT appear
    deep_files = [f for f in files if f.parent.name == "deep"]
    assert deep_files == []


def test_collect_env_files_custom_patterns(env_tree: Path):
    files = collect_env_files(env_tree, patterns=[".env.example"])
    assert all(f.name == ".env.example" for f in files)


def test_walk_env_files_raises_on_missing_dir(tmp_path: Path):
    with pytest.raises(WalkerError):
        list(walk_env_files(tmp_path / "nonexistent"))


def test_collect_env_files_raises_on_file(tmp_path: Path):
    f = tmp_path / ".env"
    f.write_text("X=1")
    with pytest.raises(WalkerError):
        collect_env_files(f)


def test_summarize_walk_returns_counts(env_tree: Path):
    info = summarize_walk(env_tree)
    assert info["total_files"] >= 3
    assert info["total_dirs"] >= 1
    assert info["root"] == str(env_tree)
    assert isinstance(info["files"], list)


def test_summarize_walk_file_paths_are_strings(env_tree: Path):
    info = summarize_walk(env_tree)
    assert all(isinstance(p, str) for p in info["files"])
