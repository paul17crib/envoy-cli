"""Unit tests for envoy.cli_walk."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envoy.cli_walk import build_parser, run_walk


@pytest.fixture()
def env_tree(tmp_path: Path) -> Path:
    (tmp_path / ".env").write_text("A=1\n")
    sub = tmp_path / "service"
    sub.mkdir()
    (sub / ".env.local").write_text("B=2\n")
    return tmp_path


def make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "root": ".",
        "max_depth": 10,
        "patterns": None,
        "include_hidden": False,
        "summary": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_parser_returns_parser():
    parser = build_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_build_parser_defaults():
    parser = build_parser()
    args = parser.parse_args([])
    assert args.root == "."
    assert args.max_depth == 10
    assert args.include_hidden is False
    assert args.summary is False


def test_run_walk_lists_files(env_tree: Path, capsys):
    args = make_args(root=str(env_tree))
    rc = run_walk(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert ".env" in out


def test_run_walk_finds_nested_file(env_tree: Path, capsys):
    args = make_args(root=str(env_tree))
    rc = run_walk(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert ".env.local" in out


def test_run_walk_returns_error_on_missing_dir(tmp_path: Path, capsys):
    args = make_args(root=str(tmp_path / "nope"))
    rc = run_walk(args)
    assert rc == 1
    assert "Error" in capsys.readouterr().err


def test_run_walk_returns_one_when_no_files(tmp_path: Path, capsys):
    args = make_args(root=str(tmp_path))
    rc = run_walk(args)
    assert rc == 1


def test_run_walk_summary_mode(env_tree: Path, capsys):
    args = make_args(root=str(env_tree), summary=True)
    rc = run_walk(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Files:" in out
    assert "Dirs:" in out


def test_run_walk_custom_pattern(env_tree: Path, capsys):
    args = make_args(root=str(env_tree), patterns=[".env.local"])
    rc = run_walk(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert ".env.local" in out


def test_run_walk_max_depth_zero(env_tree: Path, capsys):
    # depth 0 means only root; sub/.env.local should not appear
    args = make_args(root=str(env_tree), max_depth=0)
    run_walk(args)
    out = capsys.readouterr().out
    assert ".env.local" not in out
