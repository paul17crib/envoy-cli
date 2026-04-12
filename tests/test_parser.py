"""Unit tests for envoy.parser module."""

import pytest
from envoy.parser import parse_env_string, serialize_env


SAMPLE_ENV = """
# Database config
DB_HOST=localhost
DB_PORT=5432
DB_PASSWORD="s3cr3t!#safe"

# App
APP_NAME='My App'
DEBUG=false
export PATH_PREFIX=/usr/local
INLINE=value # this is a comment
"""


def test_basic_key_value():
    result = parse_env_string("KEY=value")
    assert result == {"KEY": "value"}


def test_ignores_comments():
    result = parse_env_string("# comment\nKEY=val")
    assert "# comment" not in result
    assert result["KEY"] == "val"


def test_ignores_blank_lines():
    result = parse_env_string("\n\nKEY=val\n\n")
    assert result == {"KEY": "val"}


def test_double_quoted_value():
    result = parse_env_string('SECRET="s3cr3t!#safe"')
    assert result["SECRET"] == "s3cr3t!#safe"


def test_single_quoted_value():
    result = parse_env_string("APP_NAME='My App'")
    assert result["APP_NAME"] == "My App"


def test_export_prefix():
    result = parse_env_string("export PATH_PREFIX=/usr/local")
    assert result["PATH_PREFIX"] == "/usr/local"


def test_inline_comment_stripped():
    result = parse_env_string("INLINE=value # this is a comment")
    assert result["INLINE"] == "value"


def test_empty_value():
    result = parse_env_string("EMPTY=")
    assert result["EMPTY"] == ""


def test_empty_quoted_value():
    result = parse_env_string('EMPTY=""')
    assert result["EMPTY"] == ""


def test_full_sample():
    result = parse_env_string(SAMPLE_ENV)
    assert result["DB_HOST"] == "localhost"
    assert result["DB_PORT"] == "5432"
    assert result["DB_PASSWORD"] == "s3cr3t!#safe"
    assert result["APP_NAME"] == "My App"
    assert result["DEBUG"] == "false"
    assert result["PATH_PREFIX"] == "/usr/local"
    assert result["INLINE"] == "value"


def test_serialize_simple():
    data = {"KEY": "value", "PORT": "8080"}
    output = serialize_env(data)
    assert "KEY=value" in output
    assert "PORT=8080" in output


def test_serialize_value_with_spaces():
    data = {"GREETING": "hello world"}
    output = serialize_env(data)
    assert 'GREETING="hello world"' in output


def test_roundtrip():
    original = {"HOST": "localhost", "MSG": "hello world", "TOKEN": "abc#123"}
    serialized = serialize_env(original)
    parsed = parse_env_string(serialized)
    assert parsed == original
