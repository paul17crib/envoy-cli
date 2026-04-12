"""Tests for envoy.cli_transform."""

import argparse
import pytest

from envoy.cli_transform import build_parser, run_transform
from envoy.sync import save_local


@pytest.fixture
def tmp_env_file(tmp_path):
    path = tmp_path / ".env"
    path.write_text("APP_NAME=myapp\nAPP_ENV=production\nDEBUG=false\n")
    return path


def make_args(**kwargs):
    defaults = {
        "file": ".env",
        "transforms": [],
        "keys": None,
        "dry_run": False,
        "mask": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_parser_returns_parser():
    parser = build_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_transform_upper_all_keys(tmp_env_file):
    args = make_args(file=str(tmp_env_file), transforms=["upper"])
    rc = run_transform(args)
    assert rc == 0
    content = tmp_env_file.read_text()
    assert "APP_NAME=MYAPP" in content
    assert "APP_ENV=PRODUCTION" in content


def test_transform_specific_keys_only(tmp_env_file):
    args = make_args(file=str(tmp_env_file), transforms=["upper"], keys=["APP_NAME"])
    rc = run_transform(args)
    assert rc == 0
    content = tmp_env_file.read_text()
    assert "APP_NAME=MYAPP" in content
    assert "APP_ENV=production" in content


def test_transform_dry_run_does_not_write(tmp_env_file, capsys):
    original = tmp_env_file.read_text()
    args = make_args(file=str(tmp_env_file), transforms=["upper"], dry_run=True)
    rc = run_transform(args)
    assert rc == 0
    assert tmp_env_file.read_text() == original
    out = capsys.readouterr().out
    assert "MYAPP" in out


def test_transform_no_transforms_returns_error(tmp_env_file, capsys):
    args = make_args(file=str(tmp_env_file), transforms=[])
    rc = run_transform(args)
    assert rc == 1
    assert "at least one" in capsys.readouterr().err


def test_transform_missing_file_returns_error(tmp_path, capsys):
    args = make_args(file=str(tmp_path / "missing.env"), transforms=["upper"])
    rc = run_transform(args)
    assert rc == 1


def test_transform_chained_transforms(tmp_env_file):
    args = make_args(file=str(tmp_env_file), transforms=["upper", "reverse"])
    rc = run_transform(args)
    assert rc == 0
    content = tmp_env_file.read_text()
    assert "PPAMYM" in content  # "MYAPP" reversed


def test_transform_dry_run_with_mask(tmp_env_file, capsys):
    tmp_env_file.write_text("SECRET_KEY=mysecret\n")
    args = make_args(file=str(tmp_env_file), transforms=["upper"], dry_run=True, mask=True)
    rc = run_transform(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "MYSECRET" not in out
    assert "****" in out or "***" in out
