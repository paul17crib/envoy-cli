"""Tests for envoy.zipper."""
import pytest
from envoy.zipper import zip_envs, unzip_env, get_zipped_keys, ZipperError


@pytest.fixture
def left_env():
    return {"HOST": "localhost", "PORT": "5432", "ONLY_LEFT": "yes"}


@pytest.fixture
def right_env():
    return {"HOST": "remotehost", "PORT": "5433", "ONLY_RIGHT": "no"}


def test_zip_envs_combines_shared_keys(left_env, right_env):
    result = zip_envs(left_env, right_env)
    assert result["HOST"] == "localhost|remotehost"
    assert result["PORT"] == "5432|5433"


def test_zip_envs_passes_through_left_only_keys(left_env, right_env):
    result = zip_envs(left_env, right_env)
    assert result["ONLY_LEFT"] == "yes"


def test_zip_envs_includes_right_only_keys(left_env, right_env):
    result = zip_envs(left_env, right_env)
    assert result["ONLY_RIGHT"] == "no"


def test_zip_envs_custom_delimiter(left_env, right_env):
    result = zip_envs(left_env, right_env, delimiter="::")
    assert result["HOST"] == "localhost::remotehost"


def test_zip_envs_subset_of_keys(left_env, right_env):
    result = zip_envs(left_env, right_env, keys=["HOST"])
    assert result["HOST"] == "localhost|remotehost"
    assert result["PORT"] == "5432"  # not zipped


def test_zip_envs_empty_delimiter_raises(left_env, right_env):
    with pytest.raises(ZipperError):
        zip_envs(left_env, right_env, delimiter="")


def test_zip_envs_does_not_mutate_left(left_env, right_env):
    original = dict(left_env)
    zip_envs(left_env, right_env)
    assert left_env == original


def test_unzip_env_splits_zipped_values():
    env = {"HOST": "localhost|remotehost", "PORT": "5432|5433"}
    left, right = unzip_env(env)
    assert left["HOST"] == "localhost"
    assert right["HOST"] == "remotehost"
    assert left["PORT"] == "5432"
    assert right["PORT"] == "5433"


def test_unzip_env_non_zipped_goes_to_left_only():
    env = {"HOST": "localhost|remotehost", "DEBUG": "true"}
    left, right = unzip_env(env)
    assert left["DEBUG"] == "true"
    assert "DEBUG" not in right


def test_unzip_env_custom_delimiter():
    env = {"HOST": "localhost::remotehost"}
    left, right = unzip_env(env, delimiter="::") 
    assert left["HOST"] == "localhost"
    assert right["HOST"] == "remotehost"


def test_unzip_env_subset_of_keys():
    env = {"HOST": "a|b", "PORT": "1|2"}
    left, right = unzip_env(env, keys=["HOST"])
    assert left["HOST"] == "a"
    assert right["HOST"] == "b"
    assert left["PORT"] == "1|2"  # not split
    assert "PORT" not in right


def test_unzip_env_empty_delimiter_raises():
    with pytest.raises(ZipperError):
        unzip_env({"K": "v"}, delimiter="")


def test_get_zipped_keys_returns_matching():
    env = {"HOST": "a|b", "PORT": "5432", "DB": "x|y"}
    result = get_zipped_keys(env)
    assert set(result) == {"HOST", "DB"}


def test_get_zipped_keys_empty_env():
    assert get_zipped_keys({}) == []


def test_roundtrip_preserves_values(left_env, right_env):
    zipped = zip_envs(left_env, right_env, keys=["HOST", "PORT"])
    recovered_left, recovered_right = unzip_env(zipped, keys=["HOST", "PORT"])
    assert recovered_left["HOST"] == left_env["HOST"]
    assert recovered_right["HOST"] == right_env["HOST"]
    assert recovered_left["PORT"] == left_env["PORT"]
    assert recovered_right["PORT"] == right_env["PORT"]
