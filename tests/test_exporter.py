"""Tests for envoy.exporter and envoy.cli_export2."""

from __future__ import annotations

import argparse
import pytest

from envoy.exporter import (
    ExportError,
    export_as_dotenv,
    export_as_inline,
    export_as_shell,
    export_env,
    list_schemes,
)


SAMPLE = {
    "APP_NAME": "myapp",
    "SECRET_KEY": "s3cr3t",
    "DATABASE_URL": "postgres://localhost/db",
    "DEBUG": "true",
}


def test_list_schemes_returns_known_names():
    schemes = list_schemes()
    assert "shell" in schemes
    assert "inline" in schemes
    assert "dotenv" in schemes


def test_export_as_shell_has_export_prefix():
    result = export_as_shell(SAMPLE)
    for key in SAMPLE:
        assert f"export {key}=" in result


def test_export_as_shell_masks_sensitive():
    result = export_as_shell(SAMPLE, mask=True)
    assert "s3cr3t" not in result
    assert "myapp" in result


def test_export_as_inline_single_line():
    result = export_as_inline({"A": "1", "B": "2"})
    assert "\n" not in result
    assert 'A="1"' in result
    assert 'B="2"' in result


def test_export_as_inline_masks_sensitive():
    result = export_as_inline(SAMPLE, mask=True)
    assert "s3cr3t" not in result


def test_export_as_dotenv_no_quotes_simple_value():
    result = export_as_dotenv({"KEY": "simple"})
    assert result == "KEY=simple"


def test_export_as_dotenv_quotes_value_with_space():
    result = export_as_dotenv({"KEY": "hello world"})
    assert result == 'KEY="hello world"'


def test_export_as_dotenv_quotes_value_with_hash():
    result = export_as_dotenv({"KEY": "val#ue"})
    assert 'KEY="val#ue"' in result


def test_export_as_dotenv_masks_sensitive():
    result = export_as_dotenv(SAMPLE, mask=True)
    assert "s3cr3t" not in result


def test_export_env_dispatches_by_scheme():
    result = export_env({"X": "1"}, scheme="shell")
    assert "export X=" in result


def test_export_env_unknown_scheme_raises():
    with pytest.raises(ExportError, match="Unknown export scheme"):
        export_env({"X": "1"}, scheme="xml")


def test_export_env_dotenv_scheme():
    result = export_env({"FOO": "bar"}, scheme="dotenv")
    assert "FOO=bar" in result


def test_export_env_inline_scheme():
    result = export_env({"A": "1", "B": "2"}, scheme="inline")
    assert 'A="1"' in result
    assert 'B="2"' in result


def test_export_shell_escapes_double_quotes():
    result = export_as_shell({"KEY": 'say "hello"'})
    assert '\\"hello\\"' in result
