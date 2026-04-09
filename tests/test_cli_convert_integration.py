"""Integration tests for cli_convert — round-trip and multi-format checks."""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from envoy.cli_convert import run_convert
from envoy.parser import parse_env_string


@pytest.fixture
def rich_env_file(tmp_path):
    content = (
        "# App config\n"
        "APP_NAME=envoy-cli\n"
        "APP_ENV=production\n"
        "\n"
        "# Secrets\n"
        "SECRET_KEY=supersecret\n"
        "DATABASE_URL=postgres://user:pass@localhost/db\n"
        "API_TOKEN=tok_abc123\n"
    )
    f = tmp_path / ".env"
    f.write_text(content)
    return f


def make_args(source, to_format, output=None):
    args = MagicMock()
    args.source = str(source)
    args.to_format = to_format
    args.from_format = "env"
    args.output = output
    return args


def test_round_trip_env_to_json_preserves_all_keys(rich_env_file):
    args = make_args(rich_env_file, "json")
    # capture via output file
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        out_path = f.name
    try:
        args.output = out_path
        result = run_convert(args)
        assert result == 0
        data = json.loads(Path(out_path).read_text())
        assert data["APP_NAME"] == "envoy-cli"
        assert data["SECRET_KEY"] == "supersecret"
        assert data["DATABASE_URL"] == "postgres://user:pass@localhost/db"
    finally:
        os.unlink(out_path)


def test_env_to_env_round_trip(rich_env_file, tmp_path):
    out_file = tmp_path / "out.env"
    args = make_args(rich_env_file, "env", output=str(out_file))
    result = run_convert(args)
    assert result == 0
    reparsed = parse_env_string(out_file.read_text())
    assert reparsed["APP_ENV"] == "production"
    assert reparsed["API_TOKEN"] == "tok_abc123"


def test_env_to_bash_all_keys_exported(rich_env_file, capsys):
    args = make_args(rich_env_file, "bash")
    result = run_convert(args)
    assert result == 0
    out = capsys.readouterr().out
    assert "export APP_NAME=" in out
    assert "export DATABASE_URL=" in out
    assert "export API_TOKEN=" in out


def test_env_to_yaml_contains_expected_structure(rich_env_file, capsys):
    args = make_args(rich_env_file, "yaml")
    result = run_convert(args)
    assert result == 0
    out = capsys.readouterr().out
    assert "APP_NAME" in out
    assert "envoy-cli" in out
    assert "SECRET_KEY" in out
