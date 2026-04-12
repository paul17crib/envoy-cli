"""Tests for envoy/tokenizer.py"""

import pytest

from envoy.tokenizer import (
    TokenResult,
    TokenizerError,
    get_token_counts,
    tokenize_env,
    tokenize_value,
)


# ---------------------------------------------------------------------------
# tokenize_value
# ---------------------------------------------------------------------------

def test_tokenize_value_whitespace_default():
    assert tokenize_value("hello world foo") == ["hello", "world", "foo"]


def test_tokenize_value_delimiter():
    assert tokenize_value("a,b,c", delimiter=",") == ["a", "b", "c"]


def test_tokenize_value_pattern():
    assert tokenize_value("one::two::three", pattern="::") == ["one", "two", "three"]


def test_tokenize_value_empty_string_returns_empty_list():
    assert tokenize_value("") == []


def test_tokenize_value_no_split_returns_single_token():
    assert tokenize_value("single") == ["single"]


def test_tokenize_value_invalid_pattern_raises():
    with pytest.raises(TokenizerError, match="Invalid pattern"):
        tokenize_value("abc", pattern="[invalid")


def test_tokenize_value_filters_empty_parts():
    # Multiple consecutive delimiters produce empty strings that should be dropped
    assert tokenize_value("a,,b", delimiter=",") == ["a", "b"]


# ---------------------------------------------------------------------------
# tokenize_env
# ---------------------------------------------------------------------------

def test_tokenize_env_all_keys():
    env = {"PATHS": "/usr/bin:/usr/local/bin", "TAGS": "foo bar"}
    results = tokenize_env(env, delimiter=":")
    assert "PATHS" in results
    assert results["PATHS"].tokens == ["/usr/bin", "/usr/local/bin"]
    assert "TAGS" in results
    # TAGS has no colon so it stays as one token
    assert results["TAGS"].tokens == ["/usr/bin:/usr/local/bin"[0:0]] or results["TAGS"].count() == 1


def test_tokenize_env_specific_keys():
    env = {"A": "x y z", "B": "1 2 3"}
    results = tokenize_env(env, keys=["A"])
    assert "A" in results
    assert "B" not in results


def test_tokenize_env_missing_key_raises():
    env = {"A": "hello"}
    with pytest.raises(TokenizerError, match="not found in env"):
        tokenize_env(env, keys=["MISSING"])


def test_tokenize_env_empty_env_returns_empty():
    assert tokenize_env({}) == {}


def test_tokenize_env_token_result_original_preserved():
    env = {"MSG": "hello world"}
    results = tokenize_env(env)
    assert results["MSG"].original == "hello world"


# ---------------------------------------------------------------------------
# TokenResult helpers
# ---------------------------------------------------------------------------

def test_token_result_count():
    r = TokenResult(key="K", original="a b c", tokens=["a", "b", "c"])
    assert r.count() == 3


def test_token_result_joined_default_sep():
    r = TokenResult(key="K", original="a-b", tokens=["a", "b"])
    assert r.joined() == "a b"


def test_token_result_joined_custom_sep():
    r = TokenResult(key="K", original="a-b", tokens=["a", "b"])
    assert r.joined("-") == "a-b"


# ---------------------------------------------------------------------------
# get_token_counts
# ---------------------------------------------------------------------------

def test_get_token_counts_returns_counts():
    env = {"A": "one two three", "B": "x"}
    results = tokenize_env(env)
    counts = get_token_counts(results)
    assert counts["A"] == 3
    assert counts["B"] == 1
