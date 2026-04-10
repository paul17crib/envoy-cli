"""Tests for envoy.profiler and envoy.cli_profile."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envoy.profiler import (
    DEFAULT_PROFILE,
    active_profile,
    list_profiles,
    load_profile,
    profile_path,
    save_profile,
    set_active_profile,
)
from envoy.sync import SyncError
from envoy.cli_profile import build_parser, run_profile


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def base_env(tmp_path):
    """A minimal default .env file."""
    p = tmp_path / ".env"
    p.write_text("APP_ENV=local\nDEBUG=true\n", encoding="utf-8")
    return str(p)


# ---------------------------------------------------------------------------
# profiler unit tests
# ---------------------------------------------------------------------------

def test_profile_path_default(tmp_path):
    base = str(tmp_path / ".env")
    assert profile_path(base, DEFAULT_PROFILE) == Path(base)


def test_profile_path_named(tmp_path):
    base = str(tmp_path / ".env")
    assert profile_path(base, "staging") == tmp_path / ".env.staging"


def test_list_profiles_only_default(base_env):
    assert list_profiles(base_env) == [DEFAULT_PROFILE]


def test_list_profiles_includes_named(base_env, tmp_path):
    (tmp_path / ".env.staging").write_text("APP_ENV=staging\n", encoding="utf-8")
    profiles = list_profiles(base_env)
    assert DEFAULT_PROFILE in profiles
    assert "staging" in profiles


def test_load_profile_default(base_env):
    env = load_profile(base_env, DEFAULT_PROFILE)
    assert env["APP_ENV"] == "local"
    assert env["DEBUG"] == "true"


def test_load_profile_missing_raises(base_env):
    with pytest.raises(SyncError, match="not found"):
        load_profile(base_env, "nonexistent")


def test_save_and_load_named_profile(base_env, tmp_path):
    env = {"APP_ENV": "production", "SECRET_KEY": "abc123"}
    path = save_profile(base_env, "prod", env)
    assert path.exists()
    loaded = load_profile(base_env, "prod")
    assert loaded["APP_ENV"] == "production"


def test_save_profile_no_overwrite_raises(base_env, tmp_path):
    env = {"X": "1"}
    save_profile(base_env, "qa", env)
    with pytest.raises(SyncError, match="already exists"):
        save_profile(base_env, "qa", env, overwrite=False)


def test_active_profile_unset_returns_none(base_env):
    assert active_profile(base_env) is None


def test_set_and_get_active_profile(base_env):
    set_active_profile(base_env, "staging")
    assert active_profile(base_env) == "staging"


# ---------------------------------------------------------------------------
# cli_profile tests
# ---------------------------------------------------------------------------

def _make_args(base_env, profile_cmd, **kwargs):
    ns = argparse.Namespace(file=base_env, profile_cmd=profile_cmd, **kwargs)
    return ns


def test_cli_list_profiles(base_env, capsys):
    args = _make_args(base_env, "list")
    rc = run_profile(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert DEFAULT_PROFILE in out


def test_cli_use_sets_active(base_env, capsys):
    args = _make_args(base_env, "use", name=DEFAULT_PROFILE)
    rc = run_profile(args)
    assert rc == 0
    assert active_profile(base_env) == DEFAULT_PROFILE


def test_cli_use_missing_profile_error(base_env, capsys):
    args = _make_args(base_env, "use", name="ghost")
    rc = run_profile(args)
    assert rc == 1


def test_cli_show_default_profile(base_env, capsys):
    args = _make_args(base_env, "show", name=DEFAULT_PROFILE, no_mask=True)
    rc = run_profile(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "APP_ENV" in out


def test_cli_copy_profile(base_env, tmp_path, capsys):
    args = _make_args(base_env, "copy", src=DEFAULT_PROFILE, dest="copy", overwrite=False)
    rc = run_profile(args)
    assert rc == 0
    copied = load_profile(base_env, "copy")
    assert copied["APP_ENV"] == "local"


def test_build_parser_returns_parser():
    parser = build_parser()
    assert isinstance(parser, argparse.ArgumentParser)
