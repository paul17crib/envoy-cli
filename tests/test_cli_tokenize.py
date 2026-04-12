"""Tests for envoy/cli_tokenize.py"""

import argparse
import pytest

from envoy.cli_tokenize import build_parser, run_tokenize


@pytest.fixture()
def tmp_env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text(
        "PATHS=/usr/bin:/usr/local/bin\n"
        "TAGS=alpha beta gamma\n"
        "SECRET=supersecretkey\n"
        "EMPTY=\n"
    )
    return p


def make_args(**kwargs):
    defaults = {
        "file": ".env",
        "keys": None,
        "delimiter": None,
        "pattern": None,
        "counts": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_parser_returns_parser():
    parser = build_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_tokenize_whitespace_split(tmp_env_file, capsys):
    args = make_args(file=str(tmp_env_file), keys=["TAGS"])
    rc = run_tokenize(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "TAGS" in out
    assert "'alpha'" in out
    assert "'beta'" in out
    assert "'gamma'" in out


def test_tokenize_delimiter_split(tmp_env_file, capsys):
    args = make_args(file=str(tmp_env_file), keys=["PATHS"], delimiter=":")
    rc = run_tokenize(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "'/usr/bin'" in out
    assert "'/usr/local/bin'" in out


def test_tokenize_counts_flag(tmp_env_file, capsys):
    args = make_args(file=str(tmp_env_file), keys=["TAGS"], counts=True)
    rc = run_tokenize(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "3 token(s)" in out


def test_tokenize_missing_file_returns_error(tmp_path, capsys):
    args = make_args(file=str(tmp_path / "missing.env"))
    rc = run_tokenize(args)
    assert rc == 1
    assert "Error" in capsys.readouterr().err


def test_tokenize_missing_key_returns_error(tmp_env_file, capsys):
    args = make_args(file=str(tmp_env_file), keys=["DOES_NOT_EXIST"])
    rc = run_tokenize(args)
    assert rc == 1
    assert "Error" in capsys.readouterr().err


def test_tokenize_all_keys_when_none_specified(tmp_env_file, capsys):
    args = make_args(file=str(tmp_env_file))
    rc = run_tokenize(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "PATHS" in out
    assert "TAGS" in out


def test_tokenize_pattern_split(tmp_env_file, capsys):
    args = make_args(file=str(tmp_env_file), keys=["PATHS"], pattern=r"[:/]")
    rc = run_tokenize(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "'usr'" in out


def test_tokenize_invalid_pattern_returns_error(tmp_env_file, capsys):
    args = make_args(file=str(tmp_env_file), keys=["TAGS"], pattern="[invalid")
    rc = run_tokenize(args)
    assert rc == 1
    assert "Error" in capsys.readouterr().err
