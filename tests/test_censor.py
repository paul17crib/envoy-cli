"""Tests for envoy/censor.py."""

import pytest

from envoy.censor import (
    CENSOR_PLACEHOLDER,
    CensorError,
    censor_env,
    censor_value,
    get_censored_keys,
)


@pytest.fixture()
def sample_env():
    return {
        "APP_NAME": "myapp",
        "DB_PASSWORD": "s3cr3t",
        "API_KEY": "abc123",
        "DEBUG": "true",
        "SECRET_TOKEN": "xyz",
    }


def test_censor_value_returns_placeholder():
    assert censor_value("anything") == CENSOR_PLACEHOLDER


def test_censor_value_custom_placeholder():
    assert censor_value("anything", placeholder="***") == "***"


def test_censor_env_no_selector_censors_all(sample_env):
    result = censor_env(sample_env)
    assert all(v == CENSOR_PLACEHOLDER for v in result.values())


def test_censor_env_explicit_keys(sample_env):
    result = censor_env(sample_env, keys=["DB_PASSWORD", "API_KEY"])
    assert result["DB_PASSWORD"] == CENSOR_PLACEHOLDER
    assert result["API_KEY"] == CENSOR_PLACEHOLDER
    assert result["APP_NAME"] == "myapp"
    assert result["DEBUG"] == "true"


def test_censor_env_pattern(sample_env):
    result = censor_env(sample_env, patterns=[r"secret|password"])
    assert result["DB_PASSWORD"] == CENSOR_PLACEHOLDER
    assert result["SECRET_TOKEN"] == CENSOR_PLACEHOLDER
    assert result["APP_NAME"] == "myapp"
    assert result["API_KEY"] == "abc123"


def test_censor_env_sensitive_only(sample_env):
    result = censor_env(sample_env, sensitive_only=True)
    # DB_PASSWORD, API_KEY, SECRET_TOKEN should be sensitive
    assert result["DB_PASSWORD"] == CENSOR_PLACEHOLDER
    assert result["API_KEY"] == CENSOR_PLACEHOLDER
    assert result["SECRET_TOKEN"] == CENSOR_PLACEHOLDER
    # APP_NAME and DEBUG should pass through
    assert result["APP_NAME"] == "myapp"
    assert result["DEBUG"] == "true"


def test_censor_env_does_not_mutate_original(sample_env):
    original_copy = dict(sample_env)
    censor_env(sample_env, sensitive_only=True)
    assert sample_env == original_copy


def test_censor_env_custom_placeholder(sample_env):
    result = censor_env(sample_env, keys=["DEBUG"], placeholder="REDACTED")
    assert result["DEBUG"] == "REDACTED"


def test_censor_env_invalid_pattern_raises(sample_env):
    with pytest.raises(CensorError):
        censor_env(sample_env, patterns=["[invalid"])


def test_get_censored_keys_returns_affected(sample_env):
    censored = censor_env(sample_env, keys=["DB_PASSWORD", "API_KEY"])
    affected = get_censored_keys(sample_env, censored)
    assert set(affected) == {"DB_PASSWORD", "API_KEY"}


def test_get_censored_keys_empty_when_nothing_censored(sample_env):
    affected = get_censored_keys(sample_env, dict(sample_env))
    assert affected == []


def test_censor_env_keys_and_patterns_combined(sample_env):
    result = censor_env(sample_env, keys=["DEBUG"], patterns=[r"^API_"])
    assert result["DEBUG"] == CENSOR_PLACEHOLDER
    assert result["API_KEY"] == CENSOR_PLACEHOLDER
    assert result["APP_NAME"] == "myapp"
    assert result["DB_PASSWORD"] == "s3cr3t"
