"""Tests for envoy/cli_init.py"""

import os
import io
import pytest

from envoy.cli_init import run_init, build_parser
from envoy.parser import parse_env_file, serialize_env


@pytest.fixture
def base_args(tmp_path):
    parser = build_parser()
    args = parser.parse_args(["--output", str(tmp_path / ".env")])
    return args


def test_init_creates_default_env_file(tmp_path):
    parser = build_parser()
    output = tmp_path / ".env"
    args = parser.parse_args(["--output", str(output)])
    buf = io.StringIO()
    rc = run_init(args, out=buf)
    assert rc == 0
    assert output.exists()
    assert "[ok]" in buf.getvalue()


def test_init_default_file_contains_expected_keys(tmp_path):
    parser = build_parser()
    output = tmp_path / ".env"
    args = parser.parse_args(["--output", str(output)])
    run_init(args, out=io.StringIO())
    env = parse_env_file(str(output))
    assert "APP_NAME" in env
    assert "SECRET_KEY" in env
    assert "DATABASE_URL" in env


def test_init_does_not_overwrite_existing_by_default(tmp_path):
    output = tmp_path / ".env"
    output.write_text("EXISTING=1\n")
    parser = build_parser()
    args = parser.parse_args(["--output", str(output)])
    buf = io.StringIO()
    rc = run_init(args, out=buf)
    assert rc == 1
    assert "already exists" in buf.getvalue()
    # File should be untouched
    assert output.read_text() == "EXISTING=1\n"


def test_init_overwrite_flag_replaces_file(tmp_path):
    output = tmp_path / ".env"
    output.write_text("EXISTING=1\n")
    parser = build_parser()
    args = parser.parse_args(["--output", str(output), "--overwrite"])
    buf = io.StringIO()
    rc = run_init(args, out=buf)
    assert rc == 0
    env = parse_env_file(str(output))
    assert "EXISTING" not in env
    assert "APP_NAME" in env


def test_init_from_template_blanks_values(tmp_path):
    template = tmp_path / "template.env"
    template.write_text("DB_HOST=localhost\nDB_PORT=5432\n")
    output = tmp_path / ".env"
    parser = build_parser()
    args = parser.parse_args(
        ["--output", str(output), "--template", str(template)]
    )
    buf = io.StringIO()
    rc = run_init(args, out=buf)
    assert rc == 0
    env = parse_env_file(str(output))
    assert set(env.keys()) == {"DB_HOST", "DB_PORT"}
    assert env["DB_HOST"] == ""
    assert env["DB_PORT"] == ""


def test_init_missing_template_returns_error(tmp_path):
    output = tmp_path / ".env"
    parser = build_parser()
    args = parser.parse_args(
        ["--output", str(output), "--template", str(tmp_path / "missing.env")]
    )
    buf = io.StringIO()
    rc = run_init(args, out=buf)
    assert rc == 1
    assert "not found" in buf.getvalue()


def test_build_parser_standalone():
    parser = build_parser()
    args = parser.parse_args([])
    assert args.output == ".env"
    assert args.template is None
    assert args.overwrite is False
