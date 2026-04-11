"""Tests for envoy.scoper."""

import pytest
from envoy.scoper import extract_scope, inject_scope, list_scopes, remove_scope


@pytest.fixture
def sample_env():
    return {
        "APP_NAME": "myapp",
        "APP_SECRET": "s3cr3t",
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "PLAIN": "value",
    }


# --- extract_scope ---

def test_extract_scope_returns_matching_keys(sample_env):
    result = extract_scope(sample_env, "APP")
    assert set(result.keys()) == {"APP_NAME", "APP_SECRET"}


def test_extract_scope_values_preserved(sample_env):
    result = extract_scope(sample_env, "DB")
    assert result["DB_HOST"] == "localhost"
    assert result["DB_PORT"] == "5432"


def test_extract_scope_strip_prefix(sample_env):
    result = extract_scope(sample_env, "APP", strip_prefix=True)
    assert "NAME" in result
    assert "SECRET" in result
    assert "APP_NAME" not in result


def test_extract_scope_case_insensitive_prefix(sample_env):
    result = extract_scope(sample_env, "app")
    assert "APP_NAME" in result
    assert "APP_SECRET" in result


def test_extract_scope_no_match_returns_empty(sample_env):
    result = extract_scope(sample_env, "MISSING")
    assert result == {}


def test_extract_scope_does_not_mutate_original(sample_env):
    original_keys = set(sample_env.keys())
    extract_scope(sample_env, "APP", strip_prefix=True)
    assert set(sample_env.keys()) == original_keys


# --- inject_scope ---

def test_inject_scope_adds_prefix():
    env = {"NAME": "alice", "PORT": "8080"}
    result = inject_scope(env, "APP")
    assert "APP_NAME" in result
    assert "APP_PORT" in result
    assert result["APP_NAME"] == "alice"


def test_inject_scope_does_not_double_prefix():
    env = {"APP_NAME": "already", "OTHER": "val"}
    result = inject_scope(env, "APP")
    assert "APP_NAME" in result
    assert "APP_APP_NAME" not in result
    assert "APP_OTHER" in result


def test_inject_scope_trailing_underscore_normalised():
    env = {"KEY": "v"}
    result = inject_scope(env, "PROD_")
    assert "PROD_KEY" in result


# --- list_scopes ---

def test_list_scopes_returns_sorted_prefixes(sample_env):
    scopes = list_scopes(sample_env)
    assert scopes == ["APP", "DB"]


def test_list_scopes_ignores_keys_without_underscore():
    env = {"PLAIN": "v", "APP_KEY": "v2"}
    scopes = list_scopes(env)
    assert "PLAIN" not in scopes
    assert "APP" in scopes


def test_list_scopes_empty_env_returns_empty():
    assert list_scopes({}) == []


# --- remove_scope ---

def test_remove_scope_removes_matching_keys(sample_env):
    result = remove_scope(sample_env, "APP")
    assert "APP_NAME" not in result
    assert "APP_SECRET" not in result
    assert "DB_HOST" in result


def test_remove_scope_preserves_unrelated_keys(sample_env):
    result = remove_scope(sample_env, "DB")
    assert "APP_NAME" in result
    assert "PLAIN" in result


def test_remove_scope_no_match_returns_full_env(sample_env):
    result = remove_scope(sample_env, "GHOST")
    assert result == sample_env


def test_remove_scope_does_not_mutate_original(sample_env):
    original_len = len(sample_env)
    remove_scope(sample_env, "APP")
    assert len(sample_env) == original_len
