"""Integration tests for transformer with real env data."""

import pytest

from envoy.transformer import transform_env, transform_value, TransformError


@pytest.fixture
def rich_env():
    return {
        "APP_NAME": "  my-app  ",
        "APP_VERSION": "1.0.0",
        "SECRET_KEY": "abc123",
        "DATABASE_URL": "postgres://user:pass@localhost/db",
        "DEBUG": "true",
        "EMPTY_KEY": "",
    }


def test_strip_then_upper_cleans_padded_values(rich_env):
    result = transform_env(rich_env, ["strip", "upper"], keys=["APP_NAME"])
    assert result["APP_NAME"] == "MY-APP"


def test_base64_encode_decode_roundtrip(rich_env):
    encoded = transform_env(rich_env, ["base64"], keys=["SECRET_KEY"])
    decoded = transform_env(encoded, ["unbase64"], keys=["SECRET_KEY"])
    assert decoded["SECRET_KEY"] == rich_env["SECRET_KEY"]


def test_transform_empty_value_survives(rich_env):
    result = transform_env(rich_env, ["upper"], keys=["EMPTY_KEY"])
    assert result["EMPTY_KEY"] == ""


def test_transform_all_keys_changes_each_value(rich_env):
    result = transform_env(rich_env, ["lower"])
    for key in rich_env:
        assert result[key] == rich_env[key].lower()


def test_urlencode_encodes_special_characters():
    env = {"CALLBACK_URL": "https://example.com/cb?foo=bar&baz=qux"}
    result = transform_env(env, ["urlencode"])
    assert "&" not in result["CALLBACK_URL"]
    assert "%" in result["CALLBACK_URL"]


def test_unknown_transform_raises_on_apply(rich_env):
    with pytest.raises(TransformError, match="Unknown transform"):
        transform_env(rich_env, ["nonexistent"])
