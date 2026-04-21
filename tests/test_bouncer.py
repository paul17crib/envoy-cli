"""Tests for envoy.bouncer."""

import pytest

from envoy.bouncer import (
    BouncerError,
    check_allowlist,
    check_blocklist,
    enforce_allowlist,
    enforce_blocklist,
    get_policy_violations,
)


@pytest.fixture
def sample_env():
    return {
        "APP_NAME": "myapp",
        "APP_ENV": "production",
        "DB_HOST": "localhost",
        "DB_PASSWORD": "secret",
        "DEBUG": "false",
        "SECRET_KEY": "abc123",
    }


# --- check_allowlist ---

def test_check_allowlist_returns_rejected_keys(sample_env):
    violations = check_allowlist(sample_env, [r"APP_.*", r"DEBUG"])
    assert set(violations) == {"DB_HOST", "DB_PASSWORD", "SECRET_KEY"}


def test_check_allowlist_all_match_returns_empty(sample_env):
    patterns = [r"APP_.*", r"DB_.*", r"DEBUG", r"SECRET_KEY"]
    assert check_allowlist(sample_env, patterns) == []


def test_check_allowlist_empty_patterns_rejects_all(sample_env):
    rejected = check_allowlist(sample_env, [])
    assert set(rejected) == set(sample_env.keys())


def test_check_allowlist_case_sensitive_no_match(sample_env):
    rejected = check_allowlist(sample_env, [r"app_.*"], case_sensitive=True)
    # lowercase pattern won't match uppercase keys
    assert "APP_NAME" in rejected


def test_check_allowlist_case_insensitive_matches(sample_env):
    rejected = check_allowlist(sample_env, [r"app_.*", r"db_.*", r"debug", r"secret_key"])
    assert rejected == []


# --- check_blocklist ---

def test_check_blocklist_returns_blocked_keys(sample_env):
    blocked = check_blocklist(sample_env, [r".*PASSWORD.*", r"SECRET_.*"])
    assert set(blocked) == {"DB_PASSWORD", "SECRET_KEY"}


def test_check_blocklist_no_match_returns_empty(sample_env):
    blocked = check_blocklist(sample_env, [r"NONEXISTENT_.*"])
    assert blocked == []


def test_check_blocklist_case_insensitive_default(sample_env):
    blocked = check_blocklist(sample_env, [r".*password.*"])
    assert "DB_PASSWORD" in blocked


# --- enforce_allowlist ---

def test_enforce_allowlist_keeps_matching_keys(sample_env):
    result = enforce_allowlist(sample_env, [r"APP_.*"])
    assert set(result.keys()) == {"APP_NAME", "APP_ENV"}


def test_enforce_allowlist_preserves_values(sample_env):
    result = enforce_allowlist(sample_env, [r"APP_.*"])
    assert result["APP_NAME"] == "myapp"


def test_enforce_allowlist_does_not_mutate_original(sample_env):
    original_keys = set(sample_env.keys())
    enforce_allowlist(sample_env, [r"APP_.*"])
    assert set(sample_env.keys()) == original_keys


def test_enforce_allowlist_raise_on_violation(sample_env):
    with pytest.raises(BouncerError, match="not in allowlist"):
        enforce_allowlist(sample_env, [r"APP_.*"], raise_on_violation=True)


def test_enforce_allowlist_no_violation_no_raise(sample_env):
    patterns = [r"APP_.*", r"DB_.*", r"DEBUG", r"SECRET_KEY"]
    result = enforce_allowlist(sample_env, patterns, raise_on_violation=True)
    assert len(result) == len(sample_env)


# --- enforce_blocklist ---

def test_enforce_blocklist_removes_blocked_keys(sample_env):
    result = enforce_blocklist(sample_env, [r".*PASSWORD.*", r"SECRET_.*"])
    assert "DB_PASSWORD" not in result
    assert "SECRET_KEY" not in result
    assert "APP_NAME" in result


def test_enforce_blocklist_raise_on_violation(sample_env):
    with pytest.raises(BouncerError, match="Blocked keys present"):
        enforce_blocklist(sample_env, [r"SECRET_.*"], raise_on_violation=True)


def test_enforce_blocklist_no_match_returns_full_env(sample_env):
    result = enforce_blocklist(sample_env, [r"NOPE_.*"])
    assert result == sample_env


# --- get_policy_violations ---

def test_get_policy_violations_returns_both_lists(sample_env):
    report = get_policy_violations(
        sample_env,
        allowlist=[r"APP_.*", r"DB_.*", r"DEBUG", r"SECRET_KEY"],
        blocklist=[r"SECRET_.*"],
    )
    assert report["not_allowed"] == []
    assert "SECRET_KEY" in report["blocked"]


def test_get_policy_violations_no_lists_returns_empty(sample_env):
    report = get_policy_violations(sample_env)
    assert report["not_allowed"] == []
    assert report["blocked"] == []
