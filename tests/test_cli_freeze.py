"""Tests for envoy/cli_freeze.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envoy.cli_freeze import build_parser, run_freeze
from envoy.freezer import freeze_env, FREEZE_HEADER


@pytest.fixture
def tmp_env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("APP_NAME=myapp\nSECRET_KEY=s3cr3t\nDEBUG=false\n")
    return p


@pytest.fixture
def tmp_frozen_file(tmp_path):
    env = {"APP_NAME": "myapp", "SECRET_KEY": "s3cr3t", "DEBUG": "false"}
    content = freeze_env(env, note="test freeze")
    p = tmp_path / "frozen.env"
    p.write_text(content)
    return p


def make_args(parser, *argv):
    return parser.parse_args(list(argv))


def test_build_parser_returns_parser():
    assert build_parser() is not None


def test_freeze_writes_to_stdout(tmp_env_file, capsys):
    parser = build_parser()
    args = make_args(parser, "freeze", str(tmp_env_file))
    rc = run_freeze(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert FREEZE_HEADER in out


def test_freeze_writes_to_output_file(tmp_env_file, tmp_path):
    out_path = tmp_path / "out.frozen"
    parser = build_parser()
    args = make_args(parser, "freeze", str(tmp_env_file), "--output", str(out_path))
    rc = run_freeze(args)
    assert rc == 0
    assert out_path.exists()
    assert FREEZE_HEADER in out_path.read_text()


def test_freeze_with_note_embeds_note(tmp_env_file, capsys):
    parser = build_parser()
    args = make_args(parser, "freeze", str(tmp_env_file), "--note", "prod-v2")
    run_freeze(args)
    out = capsys.readouterr().out
    payload = json.loads("\n".join(out.strip().splitlines()[1:]))
    assert payload["note"] == "prod-v2"


def test_freeze_missing_file_returns_error(tmp_path, capsys):
    parser = build_parser()
    args = make_args(parser, "freeze", str(tmp_path / "missing.env"))
    rc = run_freeze(args)
    assert rc == 1
    assert "not found" in capsys.readouterr().err


def test_thaw_writes_to_stdout(tmp_frozen_file, capsys):
    parser = build_parser()
    args = make_args(parser, "thaw", str(tmp_frozen_file))
    rc = run_freeze(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "APP_NAME" in out


def test_thaw_plain_env_returns_error(tmp_env_file, capsys):
    parser = build_parser()
    args = make_args(parser, "thaw", str(tmp_env_file))
    rc = run_freeze(args)
    assert rc == 1
    assert "not a frozen" in capsys.readouterr().err


def test_thaw_writes_to_output_file(tmp_frozen_file, tmp_path):
    out_path = tmp_path / "recovered.env"
    parser = build_parser()
    args = make_args(parser, "thaw", str(tmp_frozen_file), "--output", str(out_path))
    rc = run_freeze(args)
    assert rc == 0
    assert "APP_NAME=myapp" in out_path.read_text()


def test_info_shows_metadata(tmp_frozen_file, capsys):
    parser = build_parser()
    args = make_args(parser, "info", str(tmp_frozen_file))
    rc = run_freeze(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "Keys" in out
    assert "Frozen at" in out
    assert "test freeze" in out


def test_freeze_keys_filter(tmp_env_file, capsys):
    parser = build_parser()
    args = make_args(parser, "freeze", str(tmp_env_file), "--keys", "APP_NAME")
    rc = run_freeze(args)
    out = capsys.readouterr().out
    assert rc == 0
    payload = json.loads("\n".join(out.strip().splitlines()[1:]))
    assert list(payload["env"].keys()) == ["APP_NAME"]
