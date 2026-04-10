"""Tests for envoy.redactor."""

import pytest
from envoy.redactor import (
    redact_env,
    redact_keys,
    get_redacted_keys,
    DEFAULT_PLACEHOLDER,
)


@pytest.fixture
def sample_env():
    return {
        "APP_NAME": "myapp",
        "DATABASE_PASSWORD": "s3cr3t",
        "API_KEY": "abc123",
        "DEBUG": "true",
        "SECRET_TOKEN": "xyz789",
    }


def test_redact_env_replaces_sensitive_values(sample_env):
    result = redact_env(sample_env)
    assert result["DATABASE_PASSWORD"] == DEFAULT_PLACEHOLDER
    assert result["API_KEY"] == DEFAULT_PLACEHOLDER
    assert result["SECRET_TOKEN"] == DEFAULT_PLACEHOLDER


def test_redact_env_preserves_non_sensitive_values(sample_env):
    result = redact_env(sample_env)
    assert result["APP_NAME"] == "myapp"
    assert result["DEBUG"] == "true"


def test_redact_env_does_not_mutate_original(sample_env):
    original_copy = dict(sample_env)
    redact_env(sample_env)
    assert sample_env == original_copy


def test_redact_env_custom_placeholder(sample_env):
    result = redact_env(sample_env, placeholder="***")
    assert result["API_KEY"] == "***"
    assert result["APP_NAME"] == "myapp"


def test_redact_env_custom_patterns(sample_env):
    result = redact_env(sample_env, custom_patterns=[r"APP_NAME"])
    assert result["APP_NAME"] == DEFAULT_PLACEHOLDER


def test_redact_env_empty_dict():
    assert redact_env({}) == {}


def test_redact_keys_replaces_specified_keys(sample_env):
    result = redact_keys(sample_env, ["APP_NAME", "DEBUG"])
    assert result["APP_NAME"] == DEFAULT_PLACEHOLDER
    assert result["DEBUG"] == DEFAULT_PLACEHOLDER
    assert result["DATABASE_PASSWORD"] == "s3cr3t"


def test_redact_keys_is_case_insensitive(sample_env):
    result = redact_keys(sample_env, ["app_name"])
    assert result["APP_NAME"] == DEFAULT_PLACEHOLDER


def test_redact_keys_custom_placeholder(sample_env):
    result = redact_keys(sample_env, ["DEBUG"], placeholder="<hidden>")
    assert result["DEBUG"] == "<hidden>"


def test_redact_keys_empty_keys_list(sample_env):
    result = redact_keys(sample_env, [])
    assert result == sample_env


def test_get_redacted_keys_returns_sensitive(sample_env):
    keys = get_redacted_keys(sample_env)
    assert "DATABASE_PASSWORD" in keys
    assert "API_KEY" in keys
    assert "SECRET_TOKEN" in keys
    assert "APP_NAME" not in keys
    assert "DEBUG" not in keys


def test_get_redacted_keys_is_sorted(sample_env):
    keys = get_redacted_keys(sample_env)
    assert keys == sorted(keys)


def test_get_redacted_keys_empty_env():
    assert get_redacted_keys({}) == []
