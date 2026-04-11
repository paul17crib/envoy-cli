import pytest
from envoy.flattener import (
    flatten_nested,
    expand_flat,
    flatten_env,
    list_prefixes,
)


# ---------------------------------------------------------------------------
# flatten_nested
# ---------------------------------------------------------------------------

def test_flatten_nested_basic():
    nested = {"DB": {"HOST": "localhost", "PORT": "5432"}}
    result = flatten_nested(nested)
    assert result == {"DB__HOST": "localhost", "DB__PORT": "5432"}


def test_flatten_nested_custom_delimiter():
    nested = {"APP": {"NAME": "envoy"}}
    result = flatten_nested(nested, delimiter=".")
    assert result == {"APP.NAME": "envoy"}


def test_flatten_nested_empty_group_key():
    nested = {"": {"STANDALONE": "yes"}}
    result = flatten_nested(nested)
    assert result == {"STANDALONE": "yes"}


def test_flatten_nested_multiple_groups():
    nested = {"A": {"X": "1"}, "B": {"Y": "2"}}
    result = flatten_nested(nested)
    assert "A__X" in result and "B__Y" in result


# ---------------------------------------------------------------------------
# expand_flat
# ---------------------------------------------------------------------------

def test_expand_flat_basic():
    env = {"DB__HOST": "localhost", "DB__PORT": "5432"}
    result = expand_flat(env)
    assert result == {"DB": {"HOST": "localhost", "PORT": "5432"}}


def test_expand_flat_no_delimiter_goes_to_empty_group():
    env = {"APP_NAME": "envoy"}
    result = expand_flat(env)
    assert result == {"": {"APP_NAME": "envoy"}}


def test_expand_flat_mixed_keys():
    env = {"DB__HOST": "localhost", "STANDALONE": "yes"}
    result = expand_flat(env)
    assert "DB" in result
    assert "" in result
    assert result["DB"] == {"HOST": "localhost"}
    assert result[""] == {"STANDALONE": "yes"}


def test_expand_flat_custom_delimiter():
    env = {"APP.NAME": "envoy"}
    result = expand_flat(env, delimiter=".")
    assert result == {"APP": {"NAME": "envoy"}}


# ---------------------------------------------------------------------------
# flatten_env
# ---------------------------------------------------------------------------

def test_flatten_env_with_prefix():
    env = {"DB__HOST": "localhost", "DB__PORT": "5432", "APP_NAME": "x"}
    result = flatten_env(env, prefix="DB")
    assert result == {"HOST": "localhost", "PORT": "5432"}


def test_flatten_env_no_prefix_returns_all():
    env = {"DB__HOST": "localhost", "APP_NAME": "x"}
    result = flatten_env(env, prefix=None)
    assert result == env


def test_flatten_env_prefix_no_match_returns_empty():
    env = {"DB__HOST": "localhost"}
    result = flatten_env(env, prefix="CACHE")
    assert result == {}


# ---------------------------------------------------------------------------
# list_prefixes
# ---------------------------------------------------------------------------

def test_list_prefixes_basic():
    env = {"DB__HOST": "localhost", "APP__NAME": "envoy", "STANDALONE": "1"}
    result = list_prefixes(env)
    assert result == ["APP", "DB"]


def test_list_prefixes_no_delimited_keys():
    env = {"FOO": "bar", "BAZ": "qux"}
    result = list_prefixes(env)
    assert result == []


def test_list_prefixes_deduplicates():
    env = {"DB__HOST": "h", "DB__PORT": "p"}
    result = list_prefixes(env)
    assert result == ["DB"]
