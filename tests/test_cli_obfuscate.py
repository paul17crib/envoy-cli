"""Tests for envoy.cli_obfuscate."""

import argparse
import pytest
from unittest.mock import patch
from envoy.cli_obfuscate import build_parser, run_obfuscate


@pytest.fixture
def tmp_env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("SECRET=supersecret\nNAME=alice\nTOKEN=abc123\n")
    return str(f)


def make_args(**kwargs):
    defaults = {
        "file": ".env",
        "keys": None,
        "reveal": 4,
        "scramble": False,
        "mask_char": "*",
        "output": None,
        "dry_run": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_parser_returns_parser():
    p = build_parser()
    assert isinstance(p, argparse.ArgumentParser)


def test_obfuscate_stdout_all_keys(tmp_env_file, capsys):
    args = make_args(file=tmp_env_file, reveal=2)
    rc = run_obfuscate(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "su" in out
    assert "supersecret" not in out


def test_obfuscate_specific_keys_only(tmp_env_file, capsys):
    args = make_args(file=tmp_env_file, keys=["SECRET"], reveal=3)
    rc = run_obfuscate(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "alice" in out
    assert "supersecret" not in out


def test_obfuscate_scramble_mode(tmp_env_file, capsys):
    args = make_args(file=tmp_env_file, scramble=True)
    rc = run_obfuscate(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "supersecret" not in out
    assert "alice" not in out


def test_obfuscate_dry_run_does_not_write(tmp_env_file, capsys):
    args = make_args(file=tmp_env_file, reveal=2, dry_run=True)
    rc = run_obfuscate(args)
    assert rc == 0
    content = open(tmp_env_file).read()
    assert "supersecret" in content


def test_obfuscate_dry_run_shows_changes(tmp_env_file, capsys):
    args = make_args(file=tmp_env_file, reveal=2, dry_run=True)
    run_obfuscate(args)
    out = capsys.readouterr().out
    assert "->" in out


def test_obfuscate_output_to_file(tmp_env_file, tmp_path, capsys):
    out_file = str(tmp_path / "obfuscated.env")
    args = make_args(file=tmp_env_file, reveal=2, output=out_file)
    rc = run_obfuscate(args)
    assert rc == 0
    content = open(out_file).read()
    assert "supersecret" not in content


def test_obfuscate_missing_file_returns_error(capsys):
    args = make_args(file="/nonexistent/.env")
    rc = run_obfuscate(args)
    assert rc == 1
    err = capsys.readouterr().err
    assert "Error" in err


def test_obfuscate_custom_mask_char(tmp_env_file, capsys):
    args = make_args(file=tmp_env_file, keys=["SECRET"], reveal=2, mask_char="#")
    rc = run_obfuscate(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "#" in out
