"""Tests for envoy/cli_fmt.py"""

import io
import textwrap
from pathlib import Path

import pytest

from envoy.cli_fmt import build_parser, run_fmt


@pytest.fixture()
def tmp_env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("B=2\nA=1\nC=3\n", encoding="utf-8")
    return p


def make_args(file, check=False, stdout=False, sort=False):
    parser = build_parser()
    argv = [str(file)]
    if check:
        argv.append("--check")
    if stdout:
        argv.append("--stdout")
    if sort:
        argv.append("--sort")
    return parser.parse_args(argv)


def test_fmt_writes_formatted_file(tmp_env_file):
    args = make_args(tmp_env_file)
    out, err = io.StringIO(), io.StringIO()
    rc = run_fmt(args, stdout=out, stderr=err)
    assert rc == 0
    assert "unchanged" in out.getvalue() or "Reformatted" in out.getvalue()


def test_fmt_sort_orders_keys(tmp_env_file):
    args = make_args(tmp_env_file, sort=True)
    out, err = io.StringIO(), io.StringIO()
    rc = run_fmt(args, stdout=out, stderr=err)
    assert rc == 0
    content = tmp_env_file.read_text()
    keys = [line.split("=")[0] for line in content.splitlines() if "=" in line]
    assert keys == sorted(keys)


def test_fmt_stdout_does_not_modify_file(tmp_env_file):
    original = tmp_env_file.read_text()
    args = make_args(tmp_env_file, stdout=True)
    out, err = io.StringIO(), io.StringIO()
    rc = run_fmt(args, stdout=out, stderr=err)
    assert rc == 0
    assert tmp_env_file.read_text() == original
    assert len(out.getvalue()) > 0


def test_fmt_check_returns_zero_when_already_formatted(tmp_path):
    p = tmp_path / ".env"
    # serialize_env produces KEY=value\n lines
    p.write_text("A=1\nB=2\n", encoding="utf-8")
    args = make_args(p, check=True)
    out, err = io.StringIO(), io.StringIO()
    rc = run_fmt(args, stdout=out, stderr=err)
    assert rc == 0
    assert "already formatted" in out.getvalue()


def test_fmt_check_returns_nonzero_when_file_differs(tmp_env_file):
    # Write something that serialize_env would change (e.g. extra blank lines)
    tmp_env_file.write_text("A=1\n\n\nB=2\n", encoding="utf-8")
    args = make_args(tmp_env_file, check=True)
    out, err = io.StringIO(), io.StringIO()
    rc = run_fmt(args, stdout=out, stderr=err)
    assert rc == 1
    assert "would be reformatted" in err.getvalue()


def test_fmt_missing_file_returns_error(tmp_path):
    args = make_args(tmp_path / "nonexistent.env")
    out, err = io.StringIO(), io.StringIO()
    rc = run_fmt(args, stdout=out, stderr=err)
    assert rc == 1
    assert "not found" in err.getvalue()


def test_fmt_stdout_with_sort(tmp_env_file):
    args = make_args(tmp_env_file, stdout=True, sort=True)
    out, err = io.StringIO(), io.StringIO()
    rc = run_fmt(args, stdout=out, stderr=err)
    assert rc == 0
    keys = [line.split("=")[0] for line in out.getvalue().splitlines() if "=" in line]
    assert keys == sorted(keys)
