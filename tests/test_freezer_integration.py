"""Integration tests for freeze/thaw round-trip with realistic env data."""

from __future__ import annotations

import pytest

from envoy.freezer import freeze_env, thaw_env, is_frozen, freeze_metadata


@pytest.fixture
def rich_env():
    return {
        "APP_NAME": "envoy",
        "APP_ENV": "production",
        "SECRET_KEY": "super-secret-value-xyz",
        "DATABASE_URL": "postgres://user:pass@localhost/db",
        "REDIS_URL": "redis://localhost:6379",
        "DEBUG": "false",
        "PORT": "8080",
        "ALLOWED_HOSTS": "example.com,api.example.com",
    }


def test_integration_round_trip_preserves_all_keys(rich_env):
    frozen = freeze_env(rich_env)
    recovered = thaw_env(frozen)
    assert recovered == rich_env


def test_integration_frozen_file_is_not_parseable_as_plain_env(rich_env):
    frozen = freeze_env(rich_env)
    # A naive line-split parser would not find KEY=VALUE lines
    plain_pairs = [
        line for line in frozen.splitlines()
        if "=" in line and not line.strip().startswith("#") and not line.strip().startswith('"')
    ]
    assert len(plain_pairs) == 0


def test_integration_is_frozen_true_after_freeze(rich_env):
    frozen = freeze_env(rich_env)
    assert is_frozen(frozen)


def test_integration_subset_freeze_thaw(rich_env):
    keys = ["APP_NAME", "PORT", "DEBUG"]
    frozen = freeze_env(rich_env, keys=keys)
    recovered = thaw_env(frozen)
    assert set(recovered.keys()) == set(keys)
    for k in keys:
        assert recovered[k] == rich_env[k]


def test_integration_metadata_key_count_matches_subset(rich_env):
    keys = ["APP_NAME", "SECRET_KEY"]
    frozen = freeze_env(rich_env, keys=keys, note="partial freeze")
    meta = freeze_metadata(frozen)
    assert meta["key_count"] == 2
    assert meta["note"] == "partial freeze"


def test_integration_multiple_freeze_thaw_cycles_stable(rich_env):
    frozen1 = freeze_env(rich_env)
    thawed1 = thaw_env(frozen1)
    frozen2 = freeze_env(thawed1)
    thawed2 = thaw_env(frozen2)
    assert thawed2 == rich_env
