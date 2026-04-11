"""Tests for envoy.sorter module."""

import pytest
from envoy.sorter import sort_env, sort_by_value, sort_by_length, group_sort, get_sort_order


@pytest.fixture
def sample_env():
    return {
        "ZEBRA": "last",
        "APP_NAME": "myapp",
        "DATABASE_URL": "postgres://localhost/db",
        "app_debug": "true",
        "PORT": "8080",
    }


def test_sort_env_ascending(sample_env):
    result = sort_env(sample_env)
    keys = list(result.keys())
    assert keys == sorted(keys, key=str.lower)


def test_sort_env_descending(sample_env):
    result = sort_env(sample_env, reverse=True)
    keys = list(result.keys())
    assert keys == sorted(keys, key=str.lower, reverse=True)


def test_sort_env_case_sensitive(sample_env):
    result = sort_env(sample_env, case_sensitive=True)
    keys = list(result.keys())
    assert keys == sorted(keys)


def test_sort_env_preserves_values(sample_env):
    result = sort_env(sample_env)
    for k, v in sample_env.items():
        assert result[k] == v


def test_sort_env_does_not_mutate(sample_env):
    original_keys = list(sample_env.keys())
    sort_env(sample_env)
    assert list(sample_env.keys()) == original_keys


def test_sort_by_value_ascending():
    env = {"B": "banana", "A": "apple", "C": "cherry"}
    result = sort_by_value(env)
    values = list(result.values())
    assert values == ["apple", "banana", "cherry"]


def test_sort_by_value_descending():
    env = {"B": "banana", "A": "apple", "C": "cherry"}
    result = sort_by_value(env, reverse=True)
    values = list(result.values())
    assert values == ["cherry", "banana", "apple"]


def test_sort_by_length_short_to_long():
    env = {"LONG_KEY_NAME": "a", "B": "b", "MED_KEY": "c"}
    result = sort_by_length(env)
    keys = list(result.keys())
    assert keys == ["B", "MED_KEY", "LONG_KEY_NAME"]


def test_sort_by_length_long_to_short():
    env = {"LONG_KEY_NAME": "a", "B": "b", "MED_KEY": "c"}
    result = sort_by_length(env, reverse=True)
    keys = list(result.keys())
    assert keys == ["LONG_KEY_NAME", "MED_KEY", "B"]


def test_group_sort_clusters_by_prefix():
    env = {
        "DB_HOST": "localhost",
        "APP_NAME": "myapp",
        "DB_PORT": "5432",
        "APP_DEBUG": "true",
    }
    result = group_sort(env)
    keys = list(result.keys())
    app_idx = [keys.index(k) for k in keys if k.startswith("APP_")]
    db_idx = [keys.index(k) for k in keys if k.startswith("DB_")]
    assert max(app_idx) < min(db_idx) or max(db_idx) < min(app_idx)


def test_get_sort_order_returns_list(sample_env):
    order = get_sort_order(sample_env)
    assert isinstance(order, list)
    assert set(order) == set(sample_env.keys())


def test_sort_empty_env():
    assert sort_env({}) == {}
    assert sort_by_value({}) == {}
    assert sort_by_length({}) == {}
    assert group_sort({}) == {}
