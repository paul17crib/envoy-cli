"""Tests for converter.py"""

import json
import pytest

from envoy.converter import (
    convert,
    env_to_json,
    env_to_bash,
    env_to_docker,
    env_to_yaml,
    env_to_env,
    suggested_filename,
    FORMAT_HANDLERS,
)


SAMPLE_ENV = {
    "APP_NAME": "envoy",
    "PORT": "8080",
    "SECRET": "mysecret",
}


def test_env_to_json_valid():
    result = env_to_json(SAMPLE_ENV)
    parsed = json.loads(result)
    assert parsed["APP_NAME"] == "envoy"
    assert parsed["PORT"] == "8080"


def test_env_to_json_indented():
    result = env_to_json(SAMPLE_ENV, indent=4)
    assert "    " in result


def test_env_to_bash_has_export():
    result = env_to_bash(SAMPLE_ENV)
    assert "export APP_NAME=" in result
    assert "export PORT=" in result


def test_env_to_docker_has_env_flag():
    result = env_to_docker(SAMPLE_ENV)
    assert "--env" in result
    assert "PORT=8080" in result


def test_env_to_yaml_has_keys():
    result = env_to_yaml(SAMPLE_ENV)
    assert "APP_NAME" in result
    assert "envoy" in result


def test_env_to_env_has_assignments():
    result = env_to_env(SAMPLE_ENV)
    assert "APP_NAME=envoy" in result


def test_convert_json():
    result = convert(SAMPLE_ENV, "json")
    parsed = json.loads(result)
    assert parsed["SECRET"] == "mysecret"


def test_convert_bash():
    result = convert(SAMPLE_ENV, "bash")
    assert "export" in result


def test_convert_docker():
    result = convert(SAMPLE_ENV, "docker")
    assert "--env" in result


def test_convert_yaml():
    result = convert(SAMPLE_ENV, "yaml")
    assert "PORT" in result


def test_convert_env():
    result = convert(SAMPLE_ENV, "env")
    assert "=" in result


def test_convert_unsupported_raises():
    with pytest.raises(ValueError, match="Unsupported format"):
        convert(SAMPLE_ENV, "toml")


def test_convert_unsupported_lists_supported_in_error():
    with pytest.raises(ValueError, match="bash"):
        convert(SAMPLE_ENV, "xml")


def test_format_handlers_keys_match_expected():
    assert set(FORMAT_HANDLERS.keys()) == {"env", "bash", "docker", "yaml", "json"}


def test_suggested_filename_json():
    name = suggested_filename("myapp", "json")
    assert name.endswith(".json")


def test_suggested_filename_bash():
    name = suggested_filename("myapp", "bash")
    assert name.endswith(".sh")


def test_suggested_filename_unknown_format():
    name = suggested_filename("myapp", "unknown")
    assert name.endswith(".txt")
