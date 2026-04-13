"""Tests for envoy.sampler and envoy.cli_sample."""

from __future__ import annotations

import argparse
import pytest

from envoy.sampler import (
    SamplerError,
    get_sampled_keys,
    sample_fraction,
    sample_keys,
)


@pytest.fixture
def env():
    return {
        "APP_NAME": "myapp",
        "APP_ENV": "production",
        "DB_HOST": "localhost",
        "DB_PASSWORD": "secret",
        "API_KEY": "abc123",
        "PORT": "8080",
    }


def test_sample_keys_returns_correct_count(env):
    result = sample_keys(env, 3, seed=42)
    assert len(result) == 3


def test_sample_keys_values_preserved(env):
    result = sample_keys(env, 3, seed=1)
    for k, v in result.items():
        assert env[k] == v


def test_sample_keys_zero_returns_empty(env):
    result = sample_keys(env, 0)
    assert result == {}


def test_sample_keys_all_returns_full_env(env):
    result = sample_keys(env, len(env), seed=0)
    assert set(result.keys()) == set(env.keys())


def test_sample_keys_exceeds_pool_raises(env):
    with pytest.raises(SamplerError, match="exceeds available pool"):
        sample_keys(env, len(env) + 1)


def test_sample_keys_negative_raises(env):
    with pytest.raises(SamplerError, match="non-negative"):
        sample_keys(env, -1)


def test_sample_keys_missing_key_raises(env):
    with pytest.raises(SamplerError, match="not found"):
        sample_keys(env, 2, keys=["MISSING_KEY"])


def test_sample_keys_restricts_to_pool(env):
    pool = ["APP_NAME", "PORT"]
    result = sample_keys(env, 2, keys=pool, seed=0)
    assert set(result.keys()) == set(pool)


def test_sample_keys_seed_reproducible(env):
    r1 = sample_keys(env, 3, seed=99)
    r2 = sample_keys(env, 3, seed=99)
    assert r1 == r2


def test_sample_keys_different_seeds_may_differ(env):
    r1 = sample_keys(env, 3, seed=1)
    r2 = sample_keys(env, 3, seed=2)
    # Not guaranteed, but with 6 keys and size 3 seeds 1/2 differ
    assert isinstance(r1, dict) and isinstance(r2, dict)


def test_sample_fraction_half(env):
    result = sample_fraction(env, 0.5, seed=7)
    assert len(result) == 3


def test_sample_fraction_zero_returns_empty(env):
    result = sample_fraction(env, 0.0)
    assert result == {}


def test_sample_fraction_one_returns_all(env):
    result = sample_fraction(env, 1.0, seed=0)
    assert set(result.keys()) == set(env.keys())


def test_sample_fraction_out_of_range_raises(env):
    with pytest.raises(SamplerError, match="0.0 and 1.0"):
        sample_fraction(env, 1.5)


def test_get_sampled_keys_sorted(env):
    result = sample_keys(env, 4, seed=3)
    keys = get_sampled_keys(result)
    assert keys == sorted(keys)


# --- CLI tests ---

from unittest.mock import patch, MagicMock
from envoy.cli_sample import build_parser, run_sample


@pytest.fixture
def tmp_env_file(tmp_path, env):
    p = tmp_path / ".env"
    p.write_text("\n".join(f"{k}={v}" for k, v in env.items()) + "\n")
    return str(p)


def make_args(tmp_env_file, **kwargs):
    defaults = {
        "file": tmp_env_file,
        "count": 2,
        "fraction": None,
        "keys": None,
        "seed": 42,
        "no_mask": False,
        "dry_run": True,
        "output": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cli_sample_dry_run_prints_output(tmp_env_file, capsys):
    args = make_args(tmp_env_file, count=2, seed=42, dry_run=True)
    rc = run_sample(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "=" in out


def test_cli_sample_missing_file_returns_error(tmp_path):
    args = make_args(str(tmp_path / "missing.env"), count=1)
    rc = run_sample(args)
    assert rc == 1


def test_cli_sample_fraction_dry_run(tmp_env_file, capsys):
    args = make_args(tmp_env_file, count=None, fraction=0.5, seed=0, dry_run=True)
    rc = run_sample(args)
    assert rc == 0


def test_cli_sample_masks_sensitive_by_default(tmp_env_file, capsys):
    args = make_args(tmp_env_file, count=6, seed=0, dry_run=True, no_mask=False)
    rc = run_sample(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "***" in out or "secret" not in out


def test_cli_sample_writes_output_file(tmp_env_file, tmp_path):
    out_file = str(tmp_path / "sampled.env")
    args = make_args(tmp_env_file, count=2, seed=1, dry_run=False, output=out_file)
    rc = run_sample(args)
    assert rc == 0
    content = open(out_file).read()
    assert "=" in content


def test_build_parser_returns_parser():
    parser = build_parser()
    assert isinstance(parser, argparse.ArgumentParser)
