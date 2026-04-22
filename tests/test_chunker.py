"""Tests for envoy.chunker."""

import pytest

from envoy.chunker import ChunkerError, chunk_count, chunk_env, merge_chunks


@pytest.fixture()
def sample_env():
    return {
        "APP_NAME": "envoy",
        "APP_ENV": "production",
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_NAME": "appdb",
        "SECRET_KEY": "s3cr3t",
    }


def test_chunk_env_basic(sample_env):
    chunks = chunk_env(sample_env, 2)
    assert len(chunks) == 3
    for chunk in chunks:
        assert len(chunk) <= 2


def test_chunk_env_all_keys_present(sample_env):
    chunks = chunk_env(sample_env, 2)
    merged = {k: v for chunk in chunks for k, v in chunk.items()}
    assert merged == sample_env


def test_chunk_env_size_larger_than_env(sample_env):
    chunks = chunk_env(sample_env, 100)
    assert len(chunks) == 1
    assert chunks[0] == sample_env


def test_chunk_env_size_one(sample_env):
    chunks = chunk_env(sample_env, 1)
    assert len(chunks) == len(sample_env)
    for chunk in chunks:
        assert len(chunk) == 1


def test_chunk_env_empty_env_returns_single_empty_dict():
    chunks = chunk_env({}, 3)
    assert chunks == [{}]


def test_chunk_env_invalid_size_raises(sample_env):
    with pytest.raises(ChunkerError):
        chunk_env(sample_env, 0)


def test_chunk_env_negative_size_raises(sample_env):
    with pytest.raises(ChunkerError):
        chunk_env(sample_env, -5)


def test_chunk_env_custom_key_order(sample_env):
    keys = ["SECRET_KEY", "APP_NAME", "DB_HOST"]
    chunks = chunk_env(sample_env, 2, keys=keys)
    all_keys = [k for chunk in chunks for k in chunk]
    assert all_keys == keys


def test_chunk_env_unknown_keys_ignored(sample_env):
    chunks = chunk_env(sample_env, 3, keys=["APP_NAME", "MISSING_KEY"])
    assert len(chunks) == 1
    assert "MISSING_KEY" not in chunks[0]
    assert "APP_NAME" in chunks[0]


def test_chunk_count_basic(sample_env):
    assert chunk_count(sample_env, 2) == 3


def test_chunk_count_exact_division(sample_env):
    assert chunk_count(sample_env, 3) == 2


def test_chunk_count_empty_env():
    assert chunk_count({}, 5) == 1


def test_chunk_count_invalid_size_raises(sample_env):
    with pytest.raises(ChunkerError):
        chunk_count(sample_env, 0)


def test_merge_chunks_round_trip(sample_env):
    chunks = chunk_env(sample_env, 2)
    assert merge_chunks(chunks) == sample_env


def test_merge_chunks_later_wins_on_duplicate():
    chunks = [{"A": "1", "B": "2"}, {"A": "99"}]
    result = merge_chunks(chunks)
    assert result["A"] == "99"
    assert result["B"] == "2"


def test_merge_chunks_empty_list_returns_empty():
    assert merge_chunks([]) == {}
