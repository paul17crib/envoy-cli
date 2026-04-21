"""Tests for envoy.cli_diff4."""
import argparse
import pytest
from pathlib import Path

from envoy.cli_diff4 import build_parser, run_diff4, _colorize


@pytest.fixture()
def temp_dir(tmp_path: Path):
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


@pytest.fixture()
def env_files(temp_dir: Path):
    base = _write(temp_dir / "base.env", "A=1\nB=shared\n")
    ours = _write(temp_dir / "ours.env", "A=mine\nB=shared\n")
    theirs = _write(temp_dir / "theirs.env", "A=1\nB=shared\nC=new\n")
    return base, ours, theirs


def make_args(base, ours, theirs, no_color=True, conflicts_only=False):
    return argparse.Namespace(
        base=str(base),
        ours=str(ours),
        theirs=str(theirs),
        no_color=no_color,
        conflicts_only=conflicts_only,
    )


def test_build_parser_returns_parser():
    p = build_parser()
    assert isinstance(p, argparse.ArgumentParser)


def test_run_diff4_no_conflicts_returns_zero(env_files, capsys):
    base, ours, theirs = env_files
    args = make_args(base, ours, theirs)
    rc = run_diff4(args)
    assert rc == 0


def test_run_diff4_conflict_returns_two(temp_dir, capsys):
    base = _write(temp_dir / "b.env", "X=old\n")
    ours = _write(temp_dir / "o.env", "X=mine\n")
    theirs = _write(temp_dir / "t.env", "X=yours\n")
    args = make_args(base, ours, theirs)
    rc = run_diff4(args)
    assert rc == 2


def test_run_diff4_output_contains_key(env_files, capsys):
    base, ours, theirs = env_files
    args = make_args(base, ours, theirs)
    run_diff4(args)
    out = capsys.readouterr().out
    assert "A" in out
    assert "B" in out


def test_run_diff4_conflicts_only_hides_unchanged(env_files, capsys):
    base, ours, theirs = env_files
    args = make_args(base, ours, theirs, conflicts_only=True)
    run_diff4(args)
    out = capsys.readouterr().out
    assert "B" not in out  # B is unchanged


def test_run_diff4_missing_file_returns_one(temp_dir, capsys):
    base = _write(temp_dir / "b.env", "X=1\n")
    args = make_args(base, "/nonexistent/ours.env", "/nonexistent/theirs.env")
    rc = run_diff4(args)
    assert rc == 1


def test_colorize_no_color_returns_plain():
    result = _colorize("!", "conflict line", no_color=True)
    assert result == "conflict line"


def test_colorize_with_color_wraps_ansi():
    result = _colorize("!", "conflict line", no_color=False)
    assert "\033[" in result
    assert "conflict line" in result


def test_colorize_unchanged_no_ansi():
    result = _colorize("=", "same line", no_color=False)
    assert result == "same line"
