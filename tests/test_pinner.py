"""Unit tests for envoy.pinner."""

import json
from pathlib import Path

import pytest

from envoy.pinner import (
    PinError,
    check_drift,
    load_pins,
    pin_keys,
    save_pins,
    unpin_keys,
)


@pytest.fixture
def sample_env():
    return {"DB_HOST": "localhost", "API_KEY": "abc123", "PORT": "5432"}


def test_pin_keys_stores_values(sample_env):
    pins = pin_keys(sample_env, ["DB_HOST", "PORT"])
    assert pins["DB_HOST"] == "localhost"
    assert pins["PORT"] == "5432"


def test_pin_keys_missing_key_raises(sample_env):
    with pytest.raises(PinError, match="MISSING_KEY"):
        pin_keys(sample_env, ["MISSING_KEY"])


def test_pin_keys_merges_with_existing(sample_env):
    existing = {"API_KEY": "old"}
    pins = pin_keys(sample_env, ["DB_HOST"], existing_pins=existing)
    assert pins["API_KEY"] == "old"
    assert pins["DB_HOST"] == "localhost"


def test_pin_keys_does_not_mutate_existing(sample_env):
    existing = {"API_KEY": "old"}
    pin_keys(sample_env, ["DB_HOST"], existing_pins=existing)
    assert "DB_HOST" not in existing


def test_unpin_keys_removes_key():
    pins = {"DB_HOST": "localhost", "PORT": "5432"}
    result = unpin_keys(["PORT"], pins)
    assert "PORT" not in result
    assert "DB_HOST" in result


def test_unpin_keys_missing_raises():
    with pytest.raises(PinError, match="NOT_PINNED"):
        unpin_keys(["NOT_PINNED"], {})


def test_check_drift_no_drift(sample_env):
    pins = {"DB_HOST": "localhost", "PORT": "5432"}
    assert check_drift(sample_env, pins) == {}


def test_check_drift_detects_changed_value(sample_env):
    pins = {"DB_HOST": "remotehost"}
    drift = check_drift(sample_env, pins)
    assert "DB_HOST" in drift
    assert drift["DB_HOST"]["status"] == "changed"
    assert drift["DB_HOST"]["current"] == "localhost"


def test_check_drift_detects_missing_key():
    env = {"PORT": "5432"}
    pins = {"DB_HOST": "localhost"}
    drift = check_drift(env, pins)
    assert drift["DB_HOST"]["status"] == "missing"
    assert drift["DB_HOST"]["current"] is None


def test_save_and_load_pins(tmp_path):
    pin_file = str(tmp_path / "pins.json")
    pins = {"KEY": "value", "OTHER": "data"}
    save_pins(pins, pin_file)
    loaded = load_pins(pin_file)
    assert loaded == pins


def test_load_pins_missing_file(tmp_path):
    result = load_pins(str(tmp_path / "nonexistent.json"))
    assert result == {}


def test_load_pins_corrupt_file(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json", encoding="utf-8")
    with pytest.raises(PinError, match="Corrupt"):
        load_pins(str(bad))
