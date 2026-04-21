"""Tests for envoy.reorder."""

import pytest

from envoy.reorder import (
    ReorderError,
    get_reorder_preview,
    move_key,
    reorder_env,
)


@pytest.fixture
def sample_env():
    return {
        "APP_NAME": "myapp",
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "SECRET_KEY": "abc123",
        "DEBUG": "true",
    }


def test_reorder_env_follows_given_order(sample_env):
    order = ["DEBUG", "APP_NAME", "DB_HOST"]
    result = reorder_env(sample_env, order)
    keys = list(result.keys())
    assert keys[:3] == ["DEBUG", "APP_NAME", "DB_HOST"]


def test_reorder_env_appends_remaining_by_default(sample_env):
    order = ["DEBUG", "APP_NAME"]
    result = reorder_env(sample_env, order)
    assert set(result.keys()) == set(sample_env.keys())
    assert list(result.keys())[:2] == ["DEBUG", "APP_NAME"]


def test_reorder_env_no_append_remaining_drops_unordered(sample_env):
    order = ["APP_NAME", "DEBUG"]
    result = reorder_env(sample_env, order, append_remaining=False)
    assert list(result.keys()) == ["APP_NAME", "DEBUG"]


def test_reorder_env_preserves_values(sample_env):
    order = list(sample_env.keys())
    result = reorder_env(sample_env, order)
    for k, v in sample_env.items():
        assert result[k] == v


def test_reorder_env_missing_key_skipped_by_default(sample_env):
    order = ["NONEXISTENT", "APP_NAME"]
    result = reorder_env(sample_env, order)
    assert "NONEXISTENT" not in result
    assert "APP_NAME" in result


def test_reorder_env_missing_key_raises_when_strict(sample_env):
    with pytest.raises(ReorderError, match="NONEXISTENT"):
        reorder_env(sample_env, ["NONEXISTENT", "APP_NAME"], missing_ok=False)


def test_reorder_env_does_not_mutate_original(sample_env):
    original_keys = list(sample_env.keys())
    reorder_env(sample_env, ["DEBUG"])
    assert list(sample_env.keys()) == original_keys


def test_reorder_env_empty_order_appends_all(sample_env):
    result = reorder_env(sample_env, [])
    assert list(result.keys()) == list(sample_env.keys())


def test_get_reorder_preview_returns_key_list(sample_env):
    order = ["SECRET_KEY", "APP_NAME"]
    preview = get_reorder_preview(sample_env, order)
    assert preview[:2] == ["SECRET_KEY", "APP_NAME"]
    assert set(preview) == set(sample_env.keys())


def test_get_reorder_preview_no_append_remaining(sample_env):
    order = ["DEBUG", "DB_PORT"]
    preview = get_reorder_preview(sample_env, order, append_remaining=False)
    assert preview == ["DEBUG", "DB_PORT"]


def test_move_key_to_front(sample_env):
    result = move_key(sample_env, "SECRET_KEY", 0)
    assert list(result.keys())[0] == "SECRET_KEY"


def test_move_key_to_end(sample_env):
    result = move_key(sample_env, "APP_NAME", 999)
    assert list(result.keys())[-1] == "APP_NAME"


def test_move_key_preserves_all_keys(sample_env):
    result = move_key(sample_env, "DB_HOST", 1)
    assert set(result.keys()) == set(sample_env.keys())


def test_move_key_missing_raises():
    env = {"A": "1", "B": "2"}
    with pytest.raises(ReorderError, match="'C'"):
        move_key(env, "C", 0)
