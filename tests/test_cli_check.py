"""Unit tests for envoy.cli_check."""

import argparse
import io
import pytest

from envoy.cli_check import build_parser, run_check


@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path


def make_args(reference, target=".env", strict=False, quiet=False):
    return argparse.Namespace(
        reference=reference,
        target=target,
        strict=strict,
        quiet=quiet,
    )


def test_check_passes_when_all_keys_present(temp_dir):
    ref = temp_dir / ".env.example"
    ref.write_text("DB_HOST=\nDB_PORT=\n")
    tgt = temp_dir / ".env"
    tgt.write_text("DB_HOST=localhost\nDB_PORT=5432\n")

    out = io.StringIO()
    result = run_check(make_args(str(ref), str(tgt)), out=out)
    assert result == 0
    assert "ok" in out.getvalue()


def test_check_fails_when_keys_missing(temp_dir):
    ref = temp_dir / ".env.example"
    ref.write_text("DB_HOST=\nSECRET_KEY=\n")
    tgt = temp_dir / ".env"
    tgt.write_text("DB_HOST=localhost\n")

    out = io.StringIO()
    result = run_check(make_args(str(ref), str(tgt)), out=out)
    assert result == 1
    assert "MISSING" in out.getvalue()
    assert "SECRET_KEY" in out.getvalue()


def test_check_strict_fails_on_extra_keys(temp_dir):
    ref = temp_dir / ".env.example"
    ref.write_text("DB_HOST=\n")
    tgt = temp_dir / ".env"
    tgt.write_text("DB_HOST=localhost\nUNKNOWN_VAR=oops\n")

    out = io.StringIO()
    result = run_check(make_args(str(ref), str(tgt), strict=True), out=out)
    assert result == 1
    assert "EXTRA" in out.getvalue()
    assert "UNKNOWN_VAR" in out.getvalue()


def test_check_strict_passes_when_no_extras(temp_dir):
    ref = temp_dir / ".env.example"
    ref.write_text("DB_HOST=\n")
    tgt = temp_dir / ".env"
    tgt.write_text("DB_HOST=localhost\n")

    out = io.StringIO()
    result = run_check(make_args(str(ref), str(tgt), strict=True), out=out)
    assert result == 0


def test_check_missing_reference_returns_error(temp_dir):
    tgt = temp_dir / ".env"
    tgt.write_text("DB_HOST=localhost\n")

    out = io.StringIO()
    result = run_check(make_args(str(temp_dir / "nope.env"), str(tgt)), out=out)
    assert result == 1
    assert "error" in out.getvalue().lower()


def test_check_missing_target_returns_error(temp_dir):
    ref = temp_dir / ".env.example"
    ref.write_text("DB_HOST=\n")

    out = io.StringIO()
    result = run_check(make_args(str(ref), str(temp_dir / "nope.env")), out=out)
    assert result == 1
    assert "error" in out.getvalue().lower()


def test_check_quiet_suppresses_output(temp_dir):
    ref = temp_dir / ".env.example"
    ref.write_text("DB_HOST=\nSECRET_KEY=\n")
    tgt = temp_dir / ".env"
    tgt.write_text("DB_HOST=localhost\n")

    out = io.StringIO()
    result = run_check(make_args(str(ref), str(tgt), quiet=True), out=out)
    assert result == 1
    assert out.getvalue() == ""


def test_build_parser_returns_parser():
    parser = build_parser()
    args = parser.parse_args([".env.example", ".env", "--strict"])
    assert args.reference == ".env.example"
    assert args.target == ".env"
    assert args.strict is True
