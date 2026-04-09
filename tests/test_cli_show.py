"""Tests for envoy/cli_show.py"""

import io
import argparse
import pytest

from envoy.cli_show import build_parser, run_show


@pytest.fixture
def tmp_env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("APP_NAME=envoy\nSECRET_KEY=supersecret\nDEBUG=true\n")
    return str(p)


def make_args(**kwargs):
    defaults = {
        "file": ".env",
        "no_mask": False,
        "summary": False,
        "validate": False,
        "keys": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_show_displays_table(tmp_env_file):
    out, err = io.StringIO(), io.StringIO()
    args = make_args(file=tmp_env_file)
    rc = run_show(args, out=out, err=err)
    assert rc == 0
    output = out.getvalue()
    assert "APP_NAME" in output
    assert "DEBUG" in output


def test_show_masks_sensitive_values_by_default(tmp_env_file):
    out, err = io.StringIO(), io.StringIO()
    args = make_args(file=tmp_env_file)
    rc = run_show(args, out=out, err=err)
    assert rc == 0
    assert "supersecret" not in out.getvalue()


def test_show_no_mask_reveals_values(tmp_env_file):
    out, err = io.StringIO(), io.StringIO()
    args = make_args(file=tmp_env_file, no_mask=True)
    rc = run_show(args, out=out, err=err)
    assert rc == 0
    assert "supersecret" in out.getvalue()


def test_show_summary_mode(tmp_env_file):
    out, err = io.StringIO(), io.StringIO()
    args = make_args(file=tmp_env_file, summary=True)
    rc = run_show(args, out=out, err=err)
    assert rc == 0
    output = out.getvalue()
    # summarize_env returns a single-line string
    assert "\n" not in output.strip() or len(output.strip().splitlines()) == 1


def test_show_filter_by_keys(tmp_env_file):
    out, err = io.StringIO(), io.StringIO()
    args = make_args(file=tmp_env_file, no_mask=True, keys=["APP_NAME"])
    rc = run_show(args, out=out, err=err)
    assert rc == 0
    output = out.getvalue()
    assert "APP_NAME" in output
    assert "DEBUG" not in output


def test_show_missing_key_warns(tmp_env_file):
    out, err = io.StringIO(), io.StringIO()
    args = make_args(file=tmp_env_file, keys=["NONEXISTENT"])
    rc = run_show(args, out=out, err=err)
    assert rc == 0
    assert "NONEXISTENT" in err.getvalue()


def test_show_missing_file_returns_error():
    out, err = io.StringIO(), io.StringIO()
    args = make_args(file="/nonexistent/.env")
    rc = run_show(args, out=out, err=err)
    assert rc == 1
    assert "Error" in err.getvalue()


def test_show_validate_flag_runs_validation(tmp_path):
    p = tmp_path / ".env"
    p.write_text("1INVALID=bad\nEMPTY=\n")
    out, err = io.StringIO(), io.StringIO()
    args = make_args(file=str(p), validate=True)
    rc = run_show(args, out=out, err=err)
    # has_errors should be True for invalid key
    assert rc == 2


def test_build_parser_returns_parser():
    parser = build_parser()
    args = parser.parse_args([".env", "--no-mask", "--summary"])
    assert args.file == ".env"
    assert args.no_mask is True
    assert args.summary is True
