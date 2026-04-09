"""Tests for cli_convert.py"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from envoy.cli_convert import build_parser, convert_env, run_convert


@pytest.fixture
def tmp_env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("APP_NAME=envoy\nSECRET_KEY=abc123\nDEBUG=true\n")
    return f


def make_args(source, to_format, output=None, from_format="env"):
    args = MagicMock()
    args.source = str(source)
    args.to_format = to_format
    args.from_format = from_format
    args.output = output
    return args


def test_convert_env_to_json():
    env = {"KEY": "value", "FOO": "bar"}
    result = convert_env(env, "json")
    parsed = json.loads(result)
    assert parsed["KEY"] == "value"
    assert parsed["FOO"] == "bar"


def test_convert_env_to_bash():
    env = {"APP": "test"}
    result = convert_env(env, "bash")
    assert "export APP=" in result


def test_convert_env_to_docker():
    env = {"PORT": "8080"}
    result = convert_env(env, "docker")
    assert "--env PORT=8080" in result


def test_convert_env_to_yaml():
    env = {"DB_HOST": "localhost"}
    result = convert_env(env, "yaml")
    assert "DB_HOST" in result
    assert "localhost" in result


def test_convert_env_to_env():
    env = {"HELLO": "world"}
    result = convert_env(env, "env")
    assert "HELLO=world" in result


def test_convert_unsupported_format_raises():
    with pytest.raises(ValueError, match="Unsupported format"):
        convert_env({}, "toml")


def test_run_convert_missing_source(tmp_path):
    args = make_args(tmp_path / "missing.env", "json")
    result = run_convert(args)
    assert result == 1


def test_run_convert_to_stdout(tmp_env_file, capsys):
    args = make_args(tmp_env_file, "json")
    result = run_convert(args)
    assert result == 0
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert "APP_NAME" in parsed
    assert parsed["APP_NAME"] == "envoy"


def test_run_convert_to_output_file(tmp_env_file, tmp_path):
    out_file = tmp_path / "output.json"
    args = make_args(tmp_env_file, "json", output=str(out_file))
    result = run_convert(args)
    assert result == 0
    assert out_file.exists()
    parsed = json.loads(out_file.read_text())
    assert "SECRET_KEY" in parsed


def test_run_convert_bash_to_stdout(tmp_env_file, capsys):
    args = make_args(tmp_env_file, "bash")
    result = run_convert(args)
    assert result == 0
    captured = capsys.readouterr()
    assert "export" in captured.out


def test_build_parser_returns_parser():
    parser = build_parser()
    assert parser is not None
    parsed = parser.parse_args(["myfile.env", "--to", "json"])
    assert parsed.to_format == "json"
    assert parsed.source == "myfile.env"
