"""Tests for envoy.squasher and envoy.cli_squash."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envoy.squasher import (
    find_duplicate_keys,
    squash_lines,
    squash_env,
    format_squash_report,
)
from envoy.cli_squash import build_parser, run_squash


# ---------------------------------------------------------------------------
# find_duplicate_keys
# ---------------------------------------------------------------------------

def test_find_duplicates_detects_repeated_key():
    lines = ["FOO=1\n", "BAR=2\n", "FOO=3\n"]
    result = find_duplicate_keys(lines)
    assert "FOO" in result
    assert result["FOO"] == [0, 2]


def test_find_duplicates_ignores_unique_keys():
    lines = ["A=1\n", "B=2\n", "C=3\n"]
    assert find_duplicate_keys(lines) == {}


def test_find_duplicates_ignores_comments_and_blanks():
    lines = ["# FOO=comment\n", "\n", "FOO=real\n"]
    assert find_duplicate_keys(lines) == {}


def test_find_duplicates_multiple_keys():
    lines = ["A=1\n", "B=2\n", "A=3\n", "B=4\n", "A=5\n"]
    result = find_duplicate_keys(lines)
    assert result["A"] == [0, 2, 4]
    assert result["B"] == [1, 3]


# ---------------------------------------------------------------------------
# squash_lines
# ---------------------------------------------------------------------------

def test_squash_lines_last_keeps_last():
    lines = ["FOO=1\n", "FOO=2\n", "FOO=3\n"]
    squashed, removed = squash_lines(lines, strategy="last")
    assert squashed == ["FOO=3\n"]
    assert removed["FOO"] == 2


def test_squash_lines_first_keeps_first():
    lines = ["FOO=1\n", "FOO=2\n", "FOO=3\n"]
    squashed, removed = squash_lines(lines, strategy="first")
    assert squashed == ["FOO=1\n"]
    assert removed["FOO"] == 2


def test_squash_lines_no_duplicates_unchanged():
    lines = ["A=1\n", "B=2\n"]
    squashed, removed = squash_lines(lines)
    assert squashed == lines
    assert removed == {}


def test_squash_lines_preserves_comments_and_blanks():
    lines = ["# comment\n", "FOO=1\n", "\n", "FOO=2\n"]
    squashed, _ = squash_lines(lines, strategy="last")
    assert "# comment\n" in squashed
    assert "\n" in squashed
    assert "FOO=2\n" in squashed
    assert "FOO=1\n" not in squashed


# ---------------------------------------------------------------------------
# squash_env
# ---------------------------------------------------------------------------

def test_squash_env_returns_copy():
    env = {"A": "1", "B": "2"}
    result = squash_env(env)
    assert result == env
    assert result is not env


# ---------------------------------------------------------------------------
# format_squash_report
# ---------------------------------------------------------------------------

def test_format_squash_report_no_duplicates():
    report = format_squash_report({})
    assert "No duplicate" in report


def test_format_squash_report_with_duplicates():
    report = format_squash_report({"FOO": 2, "BAR": 1})
    assert "FOO" in report
    assert "BAR" in report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_env_file(tmp_path: Path) -> Path:
    f = tmp_path / ".env"
    f.write_text("FOO=1\nBAR=2\nFOO=3\n", encoding="utf-8")
    return f


def make_args(file: str, strategy: str = "last", dry_run: bool = False, stdout: bool = False):
    return argparse.Namespace(file=file, strategy=strategy, dry_run=dry_run, stdout=stdout)


def test_cli_squash_writes_file(tmp_env_file: Path):
    args = make_args(str(tmp_env_file))
    rc = run_squash(args)
    assert rc == 0
    content = tmp_env_file.read_text()
    assert "FOO=3" in content
    assert content.count("FOO") == 1


def test_cli_squash_dry_run_does_not_modify(tmp_env_file: Path):
    original = tmp_env_file.read_text()
    args = make_args(str(tmp_env_file), dry_run=True)
    rc = run_squash(args)
    assert rc == 0
    assert tmp_env_file.read_text() == original


def test_cli_squash_missing_file_returns_error(tmp_path: Path):
    args = make_args(str(tmp_path / "missing.env"))
    rc = run_squash(args)
    assert rc == 1


def test_build_parser_returns_parser():
    parser = build_parser()
    assert isinstance(parser, argparse.ArgumentParser)
