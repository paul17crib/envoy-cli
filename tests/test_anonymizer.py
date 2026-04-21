"""Tests for envoy.anonymizer."""

import pytest

from envoy.anonymizer import (
    AnonymizerError,
    anonymize_env,
    anonymize_value,
    get_anonymized_keys,
)


# ---------------------------------------------------------------------------
# anonymize_value
# ---------------------------------------------------------------------------

def test_anonymize_value_hash_returns_16_chars():
    result = anonymize_value("supersecret", mode="hash")
    assert len(result) == 16


def test_anonymize_value_hash_is_deterministic():
    a = anonymize_value("mysecret", mode="hash", salt="test")
    b = anonymize_value("mysecret", mode="hash", salt="test")
    assert a == b


def test_anonymize_value_hash_differs_for_different_values():
    a = anonymize_value("value1", mode="hash")
    b = anonymize_value("value2", mode="hash")
    assert a != b


def test_anonymize_value_hash_differs_for_different_salts():
    a = anonymize_value("same", mode="hash", salt="salt1")
    b = anonymize_value("same", mode="hash", salt="salt2")
    assert a != b


def test_anonymize_value_random_returns_correct_length():
    result = anonymize_value("anything", mode="random", length=16)
    assert len(result) == 16


def test_anonymize_value_random_is_not_deterministic():
    results = {anonymize_value("x", mode="random") for _ in range(10)}
    # Extremely unlikely all 10 are identical
    assert len(results) > 1


def test_anonymize_value_blank_returns_empty_string():
    assert anonymize_value("secret", mode="blank") == ""


def test_anonymize_value_unknown_mode_raises():
    with pytest.raises(AnonymizerError, match="Unknown anonymization mode"):
        anonymize_value("v", mode="rot13")


# ---------------------------------------------------------------------------
# anonymize_env
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_env():
    return {
        "APP_NAME": "myapp",
        "DB_PASSWORD": "hunter2",
        "API_KEY": "abc123",
        "DEBUG": "true",
    }


def test_anonymize_env_all_keys_by_default(sample_env):
    result = anonymize_env(sample_env, mode="hash")
    for key in sample_env:
        assert result[key] != sample_env[key] or sample_env[key] == ""


def test_anonymize_env_does_not_mutate_original(sample_env):
    original_copy = dict(sample_env)
    anonymize_env(sample_env)
    assert sample_env == original_copy


def test_anonymize_env_specific_keys_only(sample_env):
    result = anonymize_env(sample_env, keys=["DB_PASSWORD", "API_KEY"], mode="blank")
    assert result["DB_PASSWORD"] == ""
    assert result["API_KEY"] == ""
    assert result["APP_NAME"] == sample_env["APP_NAME"]
    assert result["DEBUG"] == sample_env["DEBUG"]


def test_anonymize_env_missing_key_raises(sample_env):
    with pytest.raises(AnonymizerError, match="Keys not found"):
        anonymize_env(sample_env, keys=["NONEXISTENT"])


def test_anonymize_env_empty_env_returns_empty():
    assert anonymize_env({}) == {}


# ---------------------------------------------------------------------------
# get_anonymized_keys
# ---------------------------------------------------------------------------

def test_get_anonymized_keys_returns_changed_keys(sample_env):
    anon = anonymize_env(sample_env, mode="blank")
    changed = get_anonymized_keys(sample_env, anon)
    # All non-empty values should appear as changed
    expected = [k for k, v in sample_env.items() if v != ""]
    assert set(changed) == set(expected)


def test_get_anonymized_keys_empty_when_identical(sample_env):
    changed = get_anonymized_keys(sample_env, dict(sample_env))
    assert changed == []
