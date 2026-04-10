"""Tests for envoy.cli_patch and envoy.patcher."""

from __future__ import annotations

import argparse
import os
import pytest

from envoy.cli_patch import build_parser, run_patch
from envoy.parser import serialize_env
from envoy.patcher import PatchResult, format_patch_report, patch_env


# ---------------------------------------------------------------------------
# patcher unit tests
# ---------------------------------------------------------------------------

def test_patch_env_updates_existing_key():
    base = {"A": "1", "B": "2"}
    result, report = patch_env(base, {"A": "99"})
    assert result["A"] == "99"
    assert "A" in report.applied


def test_patch_env_adds_new_key_by_default():
    base = {"A": "1"}
    result, report = patch_env(base, {"NEW": "hello"})
    assert result["NEW"] == "hello"
    assert "NEW" in report.added


def test_patch_env_no_add_skips_new_keys():
    base = {"A": "1"}
    result, report = patch_env(base, {"NEW": "hello"}, add_new=False)
    assert "NEW" not in result
    assert "NEW" in report.skipped


def test_patch_env_no_overwrite_skips_existing():
    base = {"A": "1"}
    result, report = patch_env(base, {"A": "99"}, overwrite=False)
    assert result["A"] == "1"
    assert "A" in report.skipped


def test_patch_env_keys_filter_restricts_changes():
    base = {"A": "1", "B": "2"}
    result, report = patch_env(base, {"A": "10", "B": "20"}, keys=["A"])
    assert result["A"] == "10"
    assert result["B"] == "2"
    assert "B" in report.skipped


def test_patch_env_does_not_mutate_base():
    base = {"A": "1"}
    patch_env(base, {"A": "99"})
    assert base["A"] == "1"


def test_format_patch_report_no_changes():
    report = PatchResult()
    assert "No changes" in format_patch_report(report)


def test_format_patch_report_lists_all_categories():
    report = PatchResult(applied=["A"], added=["B"], skipped=["C"])
    text = format_patch_report(report)
    assert "A" in text
    assert "B" in text
    assert "C" in text


# ---------------------------------------------------------------------------
# CLI integration tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def temp_dir(tmp_path):
    return tmp_path


def make_args(temp_dir, **kwargs):
    target = temp_dir / ".env"
    patch_file = temp_dir / "patch.env"
    target.write_text("A=1\nB=2\n")
    patch_file.write_text("B=99\nC=3\n")
    defaults = dict(
        target=str(target),
        patch_file=str(patch_file),
        no_add=False,
        no_overwrite=False,
        keys=None,
        dry_run=False,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_patch_applies_changes(temp_dir):
    args = make_args(temp_dir)
    rc = run_patch(args)
    assert rc == 0
    content = (temp_dir / ".env").read_text()
    assert "B=99" in content
    assert "C=3" in content


def test_patch_dry_run_does_not_write(temp_dir):
    args = make_args(temp_dir, dry_run=True)
    run_patch(args)
    content = (temp_dir / ".env").read_text()
    assert "B=2" in content  # original unchanged


def test_patch_missing_target_returns_error(temp_dir):
    args = make_args(temp_dir)
    args.target = str(temp_dir / "nonexistent.env")
    rc = run_patch(args)
    assert rc == 1


def test_patch_missing_patch_file_returns_error(temp_dir):
    args = make_args(temp_dir)
    args.patch_file = str(temp_dir / "nonexistent_patch.env")
    rc = run_patch(args)
    assert rc == 1


def test_build_parser_returns_parser():
    parser = build_parser()
    assert isinstance(parser, argparse.ArgumentParser)
