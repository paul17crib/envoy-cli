"""Tests for envoy/freezer.py."""

from __future__ import annotations

import json
import pytest

from envoy.freezer import (
    FREEZE_HEADER,
    FreezeError,
    freeze_env,
    freeze_metadata,
    is_frozen,
    thaw_env,
)


SAMPLE = {"APP_NAME": "myapp", "SECRET_KEY": "abc123", "DEBUG": "false"}


def test_freeze_env_produces_header():
    result = freeze_env(SAMPLE)
    assert result.startswith(FREEZE_HEADER)


def test_freeze_env_contains_all_keys():
    result = freeze_env(SAMPLE)
    payload = json.loads(result.splitlines()[1])
    assert set(payload["env"].keys()) == set(SAMPLE.keys())


def test_freeze_env_with_note():
    result = freeze_env(SAMPLE, note="production snapshot")
    payload = json.loads("\n".join(result.splitlines()[1:]))
    assert payload["note"] == "production snapshot"


def test_freeze_env_subset_of_keys():
    result = freeze_env(SAMPLE, keys=["APP_NAME", "DEBUG"])
    payload = json.loads("\n".join(result.splitlines()[1:]))
    assert "APP_NAME" in payload["env"]
    assert "SECRET_KEY" not in payload["env"]


def test_freeze_env_missing_key_raises():
    with pytest.raises(FreezeError, match="MISSING_KEY"):
        freeze_env(SAMPLE, keys=["APP_NAME", "MISSING_KEY"])


def test_thaw_env_recovers_original():
    frozen = freeze_env(SAMPLE)
    recovered = thaw_env(frozen)
    assert recovered == SAMPLE


def test_thaw_env_bad_header_raises():
    with pytest.raises(FreezeError, match="frozen env file"):
        thaw_env("APP_NAME=foo\nDEBUG=true")


def test_thaw_env_malformed_json_raises():
    bad = FREEZE_HEADER + "\n{not valid json"
    with pytest.raises(FreezeError, match="Malformed"):
        thaw_env(bad)


def test_thaw_env_missing_env_key_raises():
    payload = json.dumps({"version": 1, "frozen_at": 0, "note": ""})
    bad = FREEZE_HEADER + "\n" + payload
    with pytest.raises(FreezeError, match="missing 'env' key"):
        thaw_env(bad)


def test_is_frozen_true_for_valid():
    frozen = freeze_env(SAMPLE)
    assert is_frozen(frozen) is True


def test_is_frozen_false_for_plain_env():
    assert is_frozen("APP_NAME=myapp\nDEBUG=false") is False


def test_freeze_metadata_returns_correct_key_count():
    frozen = freeze_env(SAMPLE, note="test")
    meta = freeze_metadata(frozen)
    assert meta["key_count"] == len(SAMPLE)
    assert meta["note"] == "test"
    assert meta["version"] == 1
    assert isinstance(meta["frozen_at"], int)


def test_freeze_metadata_bad_content_raises():
    with pytest.raises(FreezeError):
        freeze_metadata("not a frozen file")


def test_freeze_env_values_preserved():
    env = {"URL": "https://example.com", "PORT": "8080"}
    frozen = freeze_env(env)
    recovered = thaw_env(frozen)
    assert recovered["URL"] == "https://example.com"
    assert recovered["PORT"] == "8080"
