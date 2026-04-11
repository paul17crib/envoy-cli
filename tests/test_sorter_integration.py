"""Integration tests for sorter module with real .env content."""

import pytest
from envoy.sorter import sort_env, group_sort, sort_by_value, sort_by_length


@pytest.fixture
def rich_env():
    return {
        "SECRET_KEY": "abc123",
        "APP_NAME": "envoy",
        "APP_DEBUG": "false",
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_NAME": "mydb",
        "PORT": "8080",
        "LOG_LEVEL": "info",
        "REDIS_URL": "redis://localhost:6379",
    }


def test_sort_env_full_ascending(rich_env):
    result = sort_env(rich_env)
    keys = list(result.keys())
    lowered = [k.lower() for k in keys]
    assert lowered == sorted(lowered)


def test_sort_env_full_descending(rich_env):
    result = sort_env(rich_env, reverse=True)
    keys = list(result.keys())
    lowered = [k.lower() for k in keys]
    assert lowered == sorted(lowered, reverse=True)


def test_group_sort_clusters_db_keys(rich_env):
    result = group_sort(rich_env)
    keys = list(result.keys())
    db_keys = [k for k in keys if k.startswith("DB_")]
    db_positions = [keys.index(k) for k in db_keys]
    assert db_positions == sorted(db_positions), "DB_ keys should be contiguous"


def test_group_sort_clusters_app_keys(rich_env):
    result = group_sort(rich_env)
    keys = list(result.keys())
    app_keys = [k for k in keys if k.startswith("APP_")]
    app_positions = [keys.index(k) for k in app_keys]
    assert app_positions == sorted(app_positions), "APP_ keys should be contiguous"


def test_sort_by_value_ordering(rich_env):
    result = sort_by_value(rich_env)
    values = [v.lower() for v in result.values()]
    assert values == sorted(values)


def test_sort_by_length_shortest_first(rich_env):
    result = sort_by_length(rich_env)
    keys = list(result.keys())
    lengths = [len(k) for k in keys]
    assert lengths == sorted(lengths)


def test_sort_does_not_lose_keys(rich_env):
    for fn in [sort_env, sort_by_value, sort_by_length, group_sort]:
        result = fn(rich_env)
        assert set(result.keys()) == set(rich_env.keys())
        assert all(result[k] == rich_env[k] for k in rich_env)
