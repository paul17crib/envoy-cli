"""Tests for envoy.aliaser."""

import pytest

from envoy.aliaser import (
    AliasError,
    add_alias,
    list_aliases,
    remove_alias,
    resolve_aliases,
)


@pytest.fixture()
def base_env() -> dict:
    return {"DB_HOST": "localhost", "DB_PORT": "5432", "APP_ENV": "production"}


# ---------------------------------------------------------------------------
# add_alias
# ---------------------------------------------------------------------------

def test_add_alias_copies_value(base_env):
    result = add_alias(base_env, "DATABASE_HOST", "DB_HOST")
    assert result["DATABASE_HOST"] == "localhost"


def test_add_alias_does_not_mutate_original(base_env):
    add_alias(base_env, "DATABASE_HOST", "DB_HOST")
    assert "DATABASE_HOST" not in base_env


def test_add_alias_preserves_existing_keys(base_env):
    result = add_alias(base_env, "DATABASE_HOST", "DB_HOST")
    assert result["DB_PORT"] == "5432"


def test_add_alias_missing_target_raises(base_env):
    with pytest.raises(AliasError, match="MISSING"):
        add_alias(base_env, "X", "MISSING")


def test_add_alias_existing_alias_raises_without_overwrite(base_env):
    with pytest.raises(AliasError, match="already exists"):
        add_alias(base_env, "DB_PORT", "DB_HOST")


def test_add_alias_overwrite_replaces_value(base_env):
    result = add_alias(base_env, "DB_PORT", "DB_HOST", overwrite=True)
    assert result["DB_PORT"] == "localhost"


def test_add_alias_same_name_raises(base_env):
    with pytest.raises(AliasError, match="must differ"):
        add_alias(base_env, "DB_HOST", "DB_HOST")


# ---------------------------------------------------------------------------
# remove_alias
# ---------------------------------------------------------------------------

def test_remove_alias_deletes_key(base_env):
    result = remove_alias(base_env, "DB_HOST")
    assert "DB_HOST" not in result


def test_remove_alias_preserves_other_keys(base_env):
    result = remove_alias(base_env, "DB_HOST")
    assert "DB_PORT" in result
    assert "APP_ENV" in result


def test_remove_alias_missing_key_raises(base_env):
    with pytest.raises(AliasError, match="not found"):
        remove_alias(base_env, "NONEXISTENT")


# ---------------------------------------------------------------------------
# resolve_aliases
# ---------------------------------------------------------------------------

def test_resolve_aliases_renames_key(base_env):
    alias_map = {"DB_HOST": "DATABASE_HOST"}
    result = resolve_aliases(base_env, alias_map)
    assert "DATABASE_HOST" in result
    assert "DB_HOST" not in result
    assert result["DATABASE_HOST"] == "localhost"


def test_resolve_aliases_canonical_wins_when_both_present():
    env = {"ALIAS_KEY": "alias_val", "REAL_KEY": "real_val"}
    alias_map = {"ALIAS_KEY": "REAL_KEY"}
    result = resolve_aliases(env, alias_map)
    assert result["REAL_KEY"] == "real_val"
    assert "ALIAS_KEY" not in result


def test_resolve_aliases_skips_absent_aliases(base_env):
    alias_map = {"GHOST": "DB_HOST"}
    result = resolve_aliases(base_env, alias_map)
    assert result == base_env


# ---------------------------------------------------------------------------
# list_aliases
# ---------------------------------------------------------------------------

def test_list_aliases_returns_present_aliases(base_env):
    alias_map = {"DB_HOST": "DATABASE_HOST", "MISSING": "SOMETHING"}
    found = list_aliases(base_env, alias_map)
    assert found == {"DB_HOST": "localhost"}


def test_list_aliases_empty_when_none_present():
    env = {"FOO": "bar"}
    found = list_aliases(env, {"ALIAS": "CANONICAL"})
    assert found == {}
