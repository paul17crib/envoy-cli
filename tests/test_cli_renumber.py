"""Tests for envoy.cli_renumber."""

import argparse

import pytest

from envoy.cli_renumber import build_parser, run_renumber
from envoy.sync import save_local


@pytest.fixture
def tmp_env_file(tmp_path):
    path = tmp_path / ".env"
    path.write_text("ITEM_1=alpha\nITEM_3=gamma\nITEM_5=epsilon\nOTHER=keep\n")
    return str(path)


def make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "file": ".env",
        "prefix": "ITEM",
        "start": 1,
        "dry_run": False,
        "gaps_only": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_parser_returns_parser():
    parser = build_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_renumber_rewrites_file(tmp_env_file):
    args = make_args(file=tmp_env_file)
    rc = run_renumber(args)
    assert rc == 0
    content = open(tmp_env_file).read()
    assert "ITEM_1" in content
    assert "ITEM_2" in content
    assert "ITEM_3" in content
    assert "ITEM_5" not in content


def test_renumber_preserves_unrelated_keys(tmp_env_file):
    args = make_args(file=tmp_env_file)
    run_renumber(args)
    content = open(tmp_env_file).read()
    assert "OTHER=keep" in content


def test_renumber_dry_run_does_not_write(tmp_env_file):
    original = open(tmp_env_file).read()
    args = make_args(file=tmp_env_file, dry_run=True)
    rc = run_renumber(args)
    assert rc == 0
    assert open(tmp_env_file).read() == original


def test_renumber_gaps_only_reports_gaps(tmp_env_file, capsys):
    args = make_args(file=tmp_env_file, gaps_only=True)
    rc = run_renumber(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Gaps" in out or "2" in out


def test_renumber_no_gaps_reports_no_changes(tmp_path):
    path = tmp_path / ".env"
    path.write_text("ITEM_1=a\nITEM_2=b\n")
    args = make_args(file=str(path))
    rc = run_renumber(args)
    assert rc == 0


def test_renumber_missing_file_returns_error(tmp_path):
    args = make_args(file=str(tmp_path / "missing.env"))
    rc = run_renumber(args)
    assert rc == 1


def test_renumber_custom_start(tmp_env_file):
    args = make_args(file=tmp_env_file, start=0)
    rc = run_renumber(args)
    assert rc == 0
    content = open(tmp_env_file).read()
    assert "ITEM_0" in content
