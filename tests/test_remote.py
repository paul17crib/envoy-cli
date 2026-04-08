"""Tests for envoy.remote providers."""

import json
import os
import pytest

from envoy.remote import FileRemoteProvider, JSONRemoteProvider


@pytest.fixture
def file_provider(tmp_path):
    return FileRemoteProvider(base_dir=str(tmp_path))


@pytest.fixture
def json_provider(tmp_path):
    return JSONRemoteProvider(json_path=str(tmp_path / "store.json"))


def test_file_provider_push_and_pull(file_provider):
    env = {"DB_HOST": "localhost", "DB_PORT": "5432"}
    file_provider.push("production", env)
    result = file_provider.pull("production")
    assert result["DB_HOST"] == "localhost"
    assert result["DB_PORT"] == "5432"


def test_file_provider_pull_missing(file_provider):
    with pytest.raises(FileNotFoundError):
        file_provider.pull("nonexistent")


def test_file_provider_creates_env_file(file_provider, tmp_path):
    file_provider.push("staging", {"KEY": "value"})
    assert os.path.exists(os.path.join(str(tmp_path), "staging.env"))


def test_json_provider_push_and_pull(json_provider):
    env = {"API_KEY": "secret", "ENV": "test"}
    json_provider.push("dev", env)
    result = json_provider.pull("dev")
    assert result["API_KEY"] == "secret"
    assert result["ENV"] == "test"


def test_json_provider_pull_missing(json_provider):
    with pytest.raises(KeyError):
        json_provider.pull("missing_env")


def test_json_provider_multiple_envs(json_provider):
    json_provider.push("dev", {"MODE": "dev"})
    json_provider.push("prod", {"MODE": "prod"})
    assert json_provider.pull("dev")["MODE"] == "dev"
    assert json_provider.pull("prod")["MODE"] == "prod"


def test_json_provider_overwrites_env(json_provider):
    json_provider.push("dev", {"X": "1"})
    json_provider.push("dev", {"X": "2"})
    assert json_provider.pull("dev")["X"] == "2"
