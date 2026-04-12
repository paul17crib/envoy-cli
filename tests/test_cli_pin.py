"""Unit tests for envoy.cli_pin."""

import argparse
import json
from pathlib import Path

import pytest

from envoy.cli_pin import build_parser, run_pin


@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def env_file(temp_dir):
    p = temp_dir / ".env"
    p.write_text("DB_HOST=localhost\nAPI_KEY=supersecret\nPORT=5432\n", encoding="utf-8")
    return str(p)


@pytest.fixture
def pin_file(temp_dir):
    return str(temp_dir / ".env.pins")


def make_args(**kwargs):
    defaults = {"action": "add", "keys": [], "file": ".env", "pin_file": ".env.pins", "no_mask": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_parser_returns_parser():
    assert isinstance(build_parser(), argparse.ArgumentParser)


def test_add_pins_keys(env_file, pin_file):
    args = make_args(action="add", keys=["DB_HOST", "PORT"], file=env_file, pin_file=pin_file)
    rc = run_pin(args)
    assert rc == 0
    pins = json.loads(Path(pin_file).read_text())
    assert pins["DB_HOST"] == "localhost"
    assert pins["PORT"] == "5432"


def test_add_missing_key_returns_error(env_file, pin_file):
    args = make_args(action="add", keys=["NONEXISTENT"], file=env_file, pin_file=pin_file)
    rc = run_pin(args)
    assert rc == 1


def test_remove_unpins_key(env_file, pin_file):
    Path(pin_file).write_text(json.dumps({"DB_HOST": "localhost", "PORT": "5432"}), encoding="utf-8")
    args = make_args(action="remove", keys=["PORT"], pin_file=pin_file)
    rc = run_pin(args)
    assert rc == 0
    pins = json.loads(Path(pin_file).read_text())
    assert "PORT" not in pins
    assert "DB_HOST" in pins


def test_remove_missing_pin_returns_error(pin_file):
    Path(pin_file).write_text(json.dumps({}), encoding="utf-8")
    args = make_args(action="remove", keys=["GHOST"], pin_file=pin_file)
    rc = run_pin(args)
    assert rc == 1


def test_check_no_drift(env_file, pin_file):
    Path(pin_file).write_text(json.dumps({"DB_HOST": "localhost"}), encoding="utf-8")
    args = make_args(action="check", file=env_file, pin_file=pin_file)
    rc = run_pin(args)
    assert rc == 0


def test_check_detects_drift(env_file, pin_file):
    Path(pin_file).write_text(json.dumps({"DB_HOST": "remotehost"}), encoding="utf-8")
    args = make_args(action="check", file=env_file, pin_file=pin_file)
    rc = run_pin(args)
    assert rc == 1


def test_check_no_pins_returns_zero(env_file, pin_file):
    args = make_args(action="check", file=env_file, pin_file=pin_file)
    rc = run_pin(args)
    assert rc == 0


def test_list_shows_pins(pin_file, capsys):
    Path(pin_file).write_text(json.dumps({"PORT": "5432"}), encoding="utf-8")
    args = make_args(action="list", pin_file=pin_file)
    rc = run_pin(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "PORT" in out


def test_list_empty_pins(pin_file, capsys):
    args = make_args(action="list", pin_file=pin_file)
    rc = run_pin(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "No keys" in out
