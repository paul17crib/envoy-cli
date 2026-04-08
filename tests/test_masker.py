"""Tests for envoy.masker module."""

import pytest
from envoy.masker import (
    is_sensitive_key,
    mask_env,
    get_masked_keys,
    MASK_VALUE,
    DEFAULT_SENSITIVE_PATTERNS,
)


@pytest.mark.parametrize(
    "key,expected",
    [
        ("DB_PASSWORD", True),
        ("API_SECRET", True),
        ("AUTH_TOKEN", True),
        ("AWS_ACCESS_KEY", True),
        ("PRIVATE_KEY", True),
        ("APP_API_KEY", True),
        ("DB_HOST", False),
        ("PORT", False),
        ("APP_NAME", False),
        ("DEBUG", False),
    ],
)
def test_is_sensitive_key(key, expected):
    assert is_sensitive_key(key) == expected


def test_is_sensitive_key_case_insensitive():
    assert is_sensitive_key("db_password") is True
    assert is_sensitive_key("Api_Secret") is True


def test_is_sensitive_key_custom_patterns():
    assert is_sensitive_key("MY_CUSTOM", [r".*CUSTOM.*"]) is True
    assert is_sensitive_key("DB_PASSWORD", [r".*CUSTOM.*"]) is False


def test_mask_env_masks_sensitive_values():
    env = {
        "DB_HOST": "localhost",
        "DB_PASSWORD": "supersecret",
        "API_KEY": "abc123",
        "PORT": "5432",
    }
    masked = mask_env(env)
    assert masked["DB_HOST"] == "localhost"
    assert masked["PORT"] == "5432"
    assert masked["DB_PASSWORD"] == MASK_VALUE
    assert masked["API_KEY"] == MASK_VALUE


def test_mask_env_does_not_mutate_original():
    env = {"DB_PASSWORD": "supersecret", "HOST": "localhost"}
    original_copy = dict(env)
    mask_env(env)
    assert env == original_copy


def test_mask_env_empty_dict():
    assert mask_env({}) == {}


def test_get_masked_keys():
    env = {
        "DB_HOST": "localhost",
        "DB_PASSWORD": "supersecret",
        "AUTH_TOKEN": "token123",
        "PORT": "5432",
    }
    masked_keys = get_masked_keys(env)
    assert masked_keys == {"DB_PASSWORD", "AUTH_TOKEN"}


def test_get_masked_keys_empty():
    env = {"HOST": "localhost", "PORT": "5432"}
    assert get_masked_keys(env) == set()
