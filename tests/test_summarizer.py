"""Tests for envoy.summarizer and envoy.cli_summarize."""

from __future__ import annotations

import argparse
import json
import os
from io import StringIO
from unittest import mock

import pytest

from envoy.summarizer import summarize, format_summary, EnvSummary, _extract_prefix
from envoy.cli_summarize import build_parser, run_summarize


# ---------------------------------------------------------------------------
# summarizer unit tests
# ---------------------------------------------------------------------------

def test_extract_prefix_returns_first_segment():
    assert _extract_prefix("DB_HOST") == "DB"


def test_extract_prefix_no_delimiter_returns_empty():
    assert _extract_prefix("NODASH") == ""


def test_extract_prefix_custom_delimiter():
    assert _extract_prefix("app.host", ".") == "app"


def test_summarize_counts_total():
    env = {"A": "1", "B": "2", "C": "3"}
    s = summarize(env)
    assert s.total == 3


def test_summarize_counts_sensitive():
    env = {"SECRET_KEY": "abc", "API_TOKEN": "xyz", "APP_NAME": "envoy"}
    s = summarize(env)
    assert s.sensitive_count == 2


def test_summarize_counts_empty_values():
    env = {"A": "", "B": "", "C": "value"}
    s = summarize(env)
    assert s.empty_count == 2
    assert s.filled_count == 1


def test_summarize_non_sensitive_count():
    env = {"SECRET": "s", "NAME": "n", "HOST": "h"}
    s = summarize(env)
    assert s.non_sensitive_count == s.total - s.sensitive_count


def test_summarize_prefixes_grouped():
    env = {"DB_HOST": "h", "DB_PORT": "5432", "APP_NAME": "x"}
    s = summarize(env)
    assert s.prefixes["DB"] == 2
    assert s.prefixes["APP"] == 1


def test_summarize_longest_key():
    env = {"SHORT": "a", "MUCH_LONGER_KEY_NAME": "b"}
    s = summarize(env)
    assert s.longest_key == "MUCH_LONGER_KEY_NAME"


def test_summarize_longest_value_key():
    env = {"A": "short", "B": "a" * 50}
    s = summarize(env)
    assert s.longest_value_key == "B"


def test_summarize_empty_env():
    s = summarize({})
    assert s.total == 0
    assert s.sensitive_count == 0
    assert s.empty_count == 0
    assert s.prefixes == {}


def test_format_summary_contains_total():
    s = EnvSummary(total=5, sensitive_count=2, empty_count=1)
    lines = format_summary(s)
    combined = "\n".join(lines)
    assert "5" in combined
    assert "2" in combined


# ---------------------------------------------------------------------------
# cli_summarize tests
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_env_file(tmp_path):
    content = "DB_HOST=localhost\nDB_PASS=secret\nAPP_NAME=envoy\nEMPTY=\n"
    p = tmp_path / ".env"
    p.write_text(content)
    return str(p)


def make_args(file, delimiter="_", as_json=False):
    return argparse.Namespace(file=file, delimiter=delimiter, as_json=as_json)


def test_run_summarize_returns_zero(tmp_env_file, capsys):
    args = make_args(tmp_env_file)
    rc = run_summarize(args)
    assert rc == 0


def test_run_summarize_prints_total(tmp_env_file, capsys):
    args = make_args(tmp_env_file)
    run_summarize(args)
    out = capsys.readouterr().out
    assert "4" in out  # 4 total keys


def test_run_summarize_json_output(tmp_env_file, capsys):
    args = make_args(tmp_env_file, as_json=True)
    rc = run_summarize(args)
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["total"] == 4
    assert "sensitive" in data
    assert "prefixes" in data


def test_run_summarize_missing_file_returns_error(tmp_path, capsys):
    args = make_args(str(tmp_path / "missing.env"))
    rc = run_summarize(args)
    assert rc == 1
    assert "Error" in capsys.readouterr().err


def test_build_parser_returns_parser():
    parser = build_parser()
    assert isinstance(parser, argparse.ArgumentParser)
