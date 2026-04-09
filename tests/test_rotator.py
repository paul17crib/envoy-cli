import pytest
from envoy.rotator import generate_secret, rotate_env, RotationPlan


def test_generate_secret_default_length():
    s = generate_secret()
    assert len(s) == 32


def test_generate_secret_custom_length():
    s = generate_secret(64)
    assert len(s) == 64


def test_generate_secret_is_alphanumeric():
    s = generate_secret(100)
    assert s.isalnum()


def test_generate_secret_values_differ():
    """Two calls should (overwhelmingly) produce different values."""
    assert generate_secret() != generate_secret()


def test_rotate_env_replaces_specified_keys():
    env = {"SECRET_KEY": "old", "DB_PASSWORD": "old", "APP_NAME": "myapp"}
    plan = rotate_env(env, ["SECRET_KEY", "DB_PASSWORD"])
    assert plan.new_env["APP_NAME"] == "myapp"
    assert plan.new_env["SECRET_KEY"] != "old"
    assert plan.new_env["DB_PASSWORD"] != "old"


def test_rotate_env_rotated_keys_list():
    env = {"SECRET_KEY": "old", "APP_NAME": "myapp"}
    plan = rotate_env(env, ["SECRET_KEY"])
    assert plan.rotated_keys == ["SECRET_KEY"]


def test_rotate_env_skips_missing_keys():
    env = {"APP_NAME": "myapp"}
    plan = rotate_env(env, ["MISSING_KEY"])
    assert plan.rotated_keys == []
    assert plan.new_env == env


def test_rotate_env_does_not_mutate_original():
    env = {"SECRET_KEY": "original"}
    rotate_env(env, ["SECRET_KEY"])
    assert env["SECRET_KEY"] == "original"


def test_rotate_env_respects_length():
    env = {"API_KEY": "short"}
    plan = rotate_env(env, ["API_KEY"], length=16)
    assert len(plan.new_env["API_KEY"]) == 16


def test_rotate_env_empty_keys_list():
    env = {"SECRET_KEY": "value"}
    plan = rotate_env(env, [])
    assert plan.rotated_keys == []
    assert plan.new_env == env
