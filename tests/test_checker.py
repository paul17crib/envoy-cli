"""Unit tests for envoy.checker."""

import pytest
from envoy.checker import check_env, missing_keys, extra_keys, CheckResult


REF = {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET_KEY": ""}
FULL = {"DB_HOST": "prod.db", "DB_PORT": "5432", "SECRET_KEY": "abc123"}
PARTIAL = {"DB_HOST": "prod.db"}
EXTRA = {"DB_HOST": "prod.db", "DB_PORT": "5432", "SECRET_KEY": "x", "EXTRA_VAR": "y"}


def test_check_env_all_present():
    result = check_env(REF, FULL)
    assert result.ok
    assert result.missing == []
    assert result.extra == []


def test_check_env_missing_keys():
    result = check_env(REF, PARTIAL)
    assert not result.ok
    assert "DB_PORT" in result.missing
    assert "SECRET_KEY" in result.missing


def test_check_env_extra_keys():
    result = check_env(REF, EXTRA)
    assert result.ok  # extra keys don't make it fail by default
    assert "EXTRA_VAR" in result.extra


def test_check_env_empty_reference():
    result = check_env({}, FULL)
    assert result.ok
    assert set(result.extra) == set(FULL.keys())


def test_check_env_empty_target():
    result = check_env(REF, {})
    assert not result.ok
    assert set(result.missing) == set(REF.keys())


def test_missing_keys_helper():
    assert missing_keys(REF, PARTIAL) == sorted(["DB_PORT", "SECRET_KEY"])


def test_extra_keys_helper():
    assert extra_keys(REF, EXTRA) == ["EXTRA_VAR"]


def test_extra_keys_none():
    assert extra_keys(REF, FULL) == []


def test_summary_missing_only():
    result = CheckResult(missing=["DB_PORT", "SECRET_KEY"], extra=["EXTRA_VAR"])
    summary = result.summary(strict=False)
    assert "MISSING" in summary
    assert "DB_PORT" in summary
    assert "EXTRA" not in summary


def test_summary_strict_includes_extra():
    result = CheckResult(missing=[], extra=["EXTRA_VAR"])
    summary = result.summary(strict=True)
    assert "EXTRA" in summary
    assert "EXTRA_VAR" in summary


def test_check_result_ok_with_extra_only():
    result = CheckResult(missing=[], extra=["X"])
    assert result.ok


def test_check_result_not_ok_with_missing():
    result = CheckResult(missing=["X"], extra=[])
    assert not result.ok
