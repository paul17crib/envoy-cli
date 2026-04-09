import pytest
import argparse
from io import StringIO
from unittest.mock import patch
from envoy.cli_search import build_parser, run_search


@pytest.fixture
def tmp_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "APP_NAME=myapp\n"
        "DATABASE_URL=postgres://localhost/db\n"
        "SECRET_KEY=supersecret\n"
        "DEBUG=true\n"
        "API_TOKEN=abc123\n"
    )
    return str(env_file)


def make_args(tmp_env_file, query, **kwargs):
    defaults = {
        "file": tmp_env_file,
        "query": query,
        "keys_only": False,
        "values_only": False,
        "no_mask": False,
        "case_sensitive": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_search_finds_matching_key(tmp_env_file):
    out = StringIO()
    args = make_args(tmp_env_file, "app_name")
    result = run_search(args, out=out)
    assert result == 0
    assert "APP_NAME" in out.getvalue()


def test_search_finds_matching_value(tmp_env_file):
    out = StringIO()
    args = make_args(tmp_env_file, "myapp")
    result = run_search(args, out=out)
    assert result == 0
    assert "APP_NAME" in out.getvalue()


def test_search_keys_only_ignores_values(tmp_env_file):
    out = StringIO()
    args = make_args(tmp_env_file, "localhost", keys_only=True)
    result = run_search(args, out=out)
    assert result == 0
    assert "No matches found" in out.getvalue()


def test_search_values_only_ignores_keys(tmp_env_file):
    out = StringIO()
    args = make_args(tmp_env_file, "debug", values_only=True)
    result = run_search(args, out=out)
    assert result == 0
    assert "No matches found" in out.getvalue()


def test_search_masks_sensitive_values_by_default(tmp_env_file):
    out = StringIO()
    args = make_args(tmp_env_file, "secret")
    run_search(args, out=out)
    assert "supersecret" not in out.getvalue()


def test_search_no_mask_reveals_sensitive_values(tmp_env_file):
    out = StringIO()
    args = make_args(tmp_env_file, "secret", no_mask=True)
    run_search(args, out=out)
    assert "supersecret" in out.getvalue()


def test_search_case_insensitive_by_default(tmp_env_file):
    out = StringIO()
    args = make_args(tmp_env_file, "APP")
    result = run_search(args, out=out)
    assert result == 0
    assert "APP_NAME" in out.getvalue()


def test_search_case_sensitive_no_match(tmp_env_file):
    out = StringIO()
    args = make_args(tmp_env_file, "app_name", case_sensitive=True)
    result = run_search(args, out=out)
    assert result == 0
    assert "No matches found" in out.getvalue()


def test_search_missing_file_returns_error(tmp_path):
    out = StringIO()
    args = make_args(str(tmp_path / "missing.env"), "anything")
    result = run_search(args, out=out)
    assert result == 1


def test_search_reports_match_count(tmp_env_file):
    out = StringIO()
    args = make_args(tmp_env_file, "_")
    run_search(args, out=out)
    output = out.getvalue()
    assert "match" in output


def test_build_parser_returns_parser():
    parser = build_parser()
    args = parser.parse_args(["myquery", "--file", ".env", "--keys-only"])
    assert args.query == "myquery"
    assert args.keys_only is True
