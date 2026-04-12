"""Integration tests for envoy/tokenizer.py"""

from envoy.tokenizer import get_token_counts, tokenize_env


rich_env = {
    "DATABASE_URL": "postgres://user:pass@localhost:5432/mydb",
    "ALLOWED_HOSTS": "localhost 127.0.0.1 example.com",
    "FEATURE_FLAGS": "feature_a,feature_b,feature_c,feature_d",
    "LOG_LEVEL": "INFO",
    "EMPTY_VAL": "",
}


def test_integration_whitespace_split_counts():
    results = tokenize_env(rich_env, keys=["ALLOWED_HOSTS"])
    assert results["ALLOWED_HOSTS"].count() == 3


def test_integration_comma_delimiter_splits_feature_flags():
    results = tokenize_env(rich_env, keys=["FEATURE_FLAGS"], delimiter=",")
    tokens = results["FEATURE_FLAGS"].tokens
    assert len(tokens) == 4
    assert "feature_a" in tokens
    assert "feature_d" in tokens


def test_integration_single_token_value():
    results = tokenize_env(rich_env, keys=["LOG_LEVEL"])
    assert results["LOG_LEVEL"].count() == 1
    assert results["LOG_LEVEL"].tokens == ["INFO"]


def test_integration_empty_value_produces_no_tokens():
    results = tokenize_env(rich_env, keys=["EMPTY_VAL"])
    assert results["EMPTY_VAL"].count() == 0
    assert results["EMPTY_VAL"].tokens == []


def test_integration_get_token_counts_all_keys():
    results = tokenize_env(rich_env, keys=["ALLOWED_HOSTS", "FEATURE_FLAGS", "LOG_LEVEL"])
    counts = get_token_counts(results)
    assert counts["ALLOWED_HOSTS"] == 3
    assert counts["FEATURE_FLAGS"] == 1  # no comma delimiter used
    assert counts["LOG_LEVEL"] == 1


def test_integration_pattern_split_url():
    results = tokenize_env(rich_env, keys=["DATABASE_URL"], pattern=r"[:/]+")
    tokens = results["DATABASE_URL"].tokens
    assert "postgres" in tokens
    assert "localhost" in tokens
    assert "mydb" in tokens


def test_integration_joined_round_trip():
    results = tokenize_env(rich_env, keys=["ALLOWED_HOSTS"])
    rejoined = results["ALLOWED_HOSTS"].joined(" ")
    assert rejoined == "localhost 127.0.0.1 example.com"
