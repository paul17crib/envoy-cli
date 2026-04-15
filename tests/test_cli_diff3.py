"""Tests for envoy.cli_diff3 (multi-file diff CLI command)."""

import argparse
import pytest
from pathlib import Path
from envoy.cli_diff3 import build_parser, run_diff3


@pytest.fixture()
def temp_dir(tmp_path):
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


@pytest.fixture()
def env_files(temp_dir):
    a = _write(temp_dir / "a.env", "APP=alpha\nDB_HOST=localhost\nSECRET_KEY=abc\n")
    b = _write(temp_dir / "b.env", "APP=alpha\nDB_HOST=remotehost\nAPI_KEY=xyz\n")
    return a, b


def make_args(files, no_color=True, no_mask=True, conflicts_only=False):
    return argparse.Namespace(
        files=[str(f) for f in files],
        no_color=no_color,
        no_mask=no_mask,
        conflicts_only=conflicts_only,
    )


def test_build_parser_returns_parser():
    p = build_parser()
    assert isinstance(p, argparse.ArgumentParser)


def test_run_diff3_returns_zero(env_files, capsys):
    a, b = env_files
    rc = run_diff3(make_args([a, b]))
    assert rc == 0


def test_run_diff3_shows_all_keys(env_files, capsys):
    a, b = env_files
    run_diff3(make_args([a, b]))
    out = capsys.readouterr().out
    assert "APP" in out
    assert "DB_HOST" in out
    assert "SECRET_KEY" in out
    assert "API_KEY" in out


def test_run_diff3_missing_shown_as_missing(env_files, capsys):
    a, b = env_files
    run_diff3(make_args([a, b]))
    out = capsys.readouterr().out
    assert "<missing>" in out


def test_run_diff3_conflicts_only_hides_consistent(env_files, capsys):
    a, b = env_files
    run_diff3(make_args([a, b], conflicts_only=True))
    out = capsys.readouterr().out
    assert "DB_HOST" in out
    assert "APP" not in out


def test_run_diff3_too_few_files_returns_error(temp_dir, capsys):
    f = _write(temp_dir / "only.env", "KEY=val\n")
    rc = run_diff3(make_args([f]))
    assert rc == 1


def test_run_diff3_missing_file_returns_error(env_files, capsys):
    a, _ = env_files
    rc = run_diff3(make_args([a, "/no/such/file.env"]))
    assert rc == 1
    err = capsys.readouterr().err
    assert "not found" in err


def test_run_diff3_three_files(temp_dir, capsys):
    a = _write(temp_dir / "a.env", "KEY=1\n")
    b = _write(temp_dir / "b.env", "KEY=2\n")
    c = _write(temp_dir / "c.env", "KEY=1\nEXTRA=yes\n")
    rc = run_diff3(make_args([a, b, c]))
    assert rc == 0
    out = capsys.readouterr().out
    assert "EXTRA" in out
