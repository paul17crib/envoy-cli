"""Tests for envoy.cli_diff2 module."""

import argparse
import pytest
from unittest.mock import patch, MagicMock

from envoy.cli_diff2 import build_parser, run_diff2, _colorize
from envoy.sync import SyncError


@pytest.fixture
def temp_envs(tmp_path):
    base = tmp_path / ".env.base"
    base.write_text("APP_NAME=myapp\nSECRET_KEY=abc123\nOLD_KEY=old\n")
    target = tmp_path / ".env.target"
    target.write_text("APP_NAME=myapp\nSECRET_KEY=xyz789\nNEW_KEY=new\n")
    return str(base), str(target)


def make_args(base, target, no_mask=False, unchanged=False, no_color=True):
    return argparse.Namespace(
        base=base,
        target=target,
        no_mask=no_mask,
        unchanged=unchanged,
        no_color=no_color,
    )


def test_build_parser_returns_parser():
    parser = build_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_colorize_no_color_returns_plain():
    assert _colorize("+", "hello", no_color=True) == "hello"


def test_colorize_with_color_wraps_ansi():
    result = _colorize("+", "hello", no_color=False)
    assert "hello" in result
    assert "\033[" in result


def test_colorize_unknown_symbol_returns_plain():
    assert _colorize("?", "hello", no_color=False) == "hello"


def test_diff2_shows_added_removed_changed(temp_envs, capsys):
    base, target = temp_envs
    args = make_args(base, target, no_mask=True)
    rc = run_diff2(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "+" in out  # NEW_KEY added
    assert "-" in out  # OLD_KEY removed
    assert "~" in out  # SECRET_KEY changed


def test_diff2_masks_sensitive_values_by_default(temp_envs, capsys):
    base, target = temp_envs
    args = make_args(base, target, no_mask=False)
    run_diff2(args)
    out = capsys.readouterr().out
    assert "abc123" not in out
    assert "xyz789" not in out


def test_diff2_no_mask_reveals_values(temp_envs, capsys):
    base, target = temp_envs
    args = make_args(base, target, no_mask=True)
    run_diff2(args)
    out = capsys.readouterr().out
    assert "abc123" in out or "xyz789" in out


def test_diff2_identical_files_reports_no_diff(tmp_path, capsys):
    f = tmp_path / ".env"
    f.write_text("A=1\nB=2\n")
    args = make_args(str(f), str(f))
    rc = run_diff2(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "No differences found" in out


def test_diff2_missing_base_returns_error(tmp_path, capsys):
    target = tmp_path / ".env"
    target.write_text("A=1\n")
    args = make_args("/nonexistent/.env", str(target))
    rc = run_diff2(args)
    assert rc == 1
    assert "Error" in capsys.readouterr().err


def test_diff2_missing_target_returns_error(tmp_path, capsys):
    base = tmp_path / ".env"
    base.write_text("A=1\n")
    args = make_args(str(base), "/nonexistent/.env")
    rc = run_diff2(args)
    assert rc == 1


def test_diff2_unchanged_flag_shows_equal_keys(tmp_path, capsys):
    f1 = tmp_path / "a.env"
    f1.write_text("SHARED=same\nONLY_A=1\n")
    f2 = tmp_path / "b.env"
    f2.write_text("SHARED=same\nONLY_B=2\n")
    args = make_args(str(f1), str(f2), no_mask=True, unchanged=True)
    run_diff2(args)
    out = capsys.readouterr().out
    assert "= SHARED" in out


def test_diff2_summary_line_present(temp_envs, capsys):
    base, target = temp_envs
    args = make_args(base, target, no_mask=True)
    run_diff2(args)
    out = capsys.readouterr().out
    assert "Summary:" in out
