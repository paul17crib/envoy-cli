"""Tests for envoy.encoder."""

import base64
import urllib.parse

import pytest

from envoy.encoder import (
    EncoderError,
    decode_env,
    decode_value,
    encode_env,
    encode_value,
    get_encoded_keys,
    list_schemes,
)


def test_list_schemes_returns_known_names():
    schemes = list_schemes()
    assert "base64" in schemes
    assert "urlencode" in schemes
    assert "hex" in schemes
    assert "base64url" in schemes


def test_encode_value_base64():
    result = encode_value("hello", "base64")
    assert result == base64.b64encode(b"hello").decode()


def test_decode_value_base64_roundtrip():
    encoded = encode_value("supersecret", "base64")
    assert decode_value(encoded, "base64") == "supersecret"


def test_encode_value_hex():
    result = encode_value("abc", "hex")
    assert result == b"abc".hex()


def test_decode_value_hex_roundtrip():
    encoded = encode_value("my_value", "hex")
    assert decode_value(encoded, "hex") == "my_value"


def test_encode_value_urlencode():
    result = encode_value("hello world", "urlencode")
    assert result == "hello%20world"


def test_decode_value_urlencode():
    assert decode_value("hello%20world", "urlencode") == "hello world"


def test_encode_value_base64url_roundtrip():
    original = "data+with/special=chars"
    encoded = encode_value(original, "base64url")
    assert decode_value(encoded, "base64url") == original


def test_encode_value_unknown_scheme_raises():
    with pytest.raises(EncoderError, match="Unknown encoding scheme"):
        encode_value("value", "rot13")


def test_decode_value_unknown_scheme_raises():
    with pytest.raises(EncoderError, match="Unknown encoding scheme"):
        decode_value("value", "rot13")


def test_encode_env_encodes_all_keys():
    env = {"A": "hello", "B": "world"}
    result = encode_env(env, "base64")
    assert result["A"] == encode_value("hello", "base64")
    assert result["B"] == encode_value("world", "base64")


def test_encode_env_does_not_mutate_original():
    env = {"A": "hello"}
    encode_env(env, "base64")
    assert env["A"] == "hello"


def test_encode_env_keys_filter_limits_scope():
    env = {"A": "hello", "B": "world"}
    result = encode_env(env, "base64", keys=["A"])
    assert result["A"] != "hello"
    assert result["B"] == "world"


def test_decode_env_roundtrip():
    env = {"SECRET": "topsecret", "NAME": "envoy"}
    encoded = encode_env(env, "hex")
    decoded = decode_env(encoded, "hex")
    assert decoded == env


def test_get_encoded_keys_returns_changed_keys():
    original = {"A": "hello", "B": "world"}
    encoded = encode_env(original, "base64", keys=["A"])
    changed = get_encoded_keys(original, encoded)
    assert changed == ["A"]


def test_get_encoded_keys_empty_when_no_change():
    env = {"A": "same"}
    assert get_encoded_keys(env, dict(env)) == []
