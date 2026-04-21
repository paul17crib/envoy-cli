"""Tests for envoy.classifier and envoy.cli_classify."""

from __future__ import annotations

import argparse

import pytest

from envoy.classifier import (
    ClassifiedKey,
    classify_env,
    classify_key,
    group_by_category,
    list_categories,
)
from envoy.cli_classify import build_parser, run_classify


# ---------------------------------------------------------------------------
# classify_key
# ---------------------------------------------------------------------------

def test_classify_key_database():
    assert classify_key("DATABASE_URL") == "database"


def test_classify_key_auth():
    assert classify_key("SECRET_KEY") == "auth"


def test_classify_key_network():
    assert classify_key("API_HOST") == "network"


def test_classify_key_general_fallback():
    assert classify_key("APP_NAME") == "general"


def test_classify_key_feature_flag():
    assert classify_key("FEATURE_DARK_MODE") == "feature"


# ---------------------------------------------------------------------------
# classify_env
# ---------------------------------------------------------------------------

def test_classify_env_returns_classified_keys():
    env = {"DB_HOST": "localhost", "APP_NAME": "myapp"}
    result = classify_env(env)
    assert "DB_HOST" in result
    assert isinstance(result["DB_HOST"], ClassifiedKey)


def test_classify_env_marks_sensitive_keys():
    env = {"SECRET_KEY": "abc123", "APP_NAME": "myapp"}
    result = classify_env(env)
    assert result["SECRET_KEY"].sensitive is True
    assert result["APP_NAME"].sensitive is False


def test_classify_env_extra_patterns():
    env = {"WIDGET_COLOR": "blue"}
    result = classify_env(env, extra_patterns={"ui": ["widget", "color"]})
    assert result["WIDGET_COLOR"].category == "ui"


def test_classify_env_does_not_mutate_original():
    env = {"DB_URL": "postgres://localhost"}
    original = dict(env)
    classify_env(env)
    assert env == original


# ---------------------------------------------------------------------------
# group_by_category
# ---------------------------------------------------------------------------

def test_group_by_category_groups_correctly():
    env = {"DB_HOST": "localhost", "DB_PASS": "secret", "APP_NAME": "x"}
    classified = classify_env(env)
    groups = group_by_category(classified)
    assert "database" in groups or "network" in groups
    assert "general" in groups


def test_group_by_category_all_keys_present():
    env = {"A": "1", "B": "2", "LOG_LEVEL": "info"}
    classified = classify_env(env)
    groups = group_by_category(classified)
    total = sum(len(v) for v in groups.values())
    assert total == len(env)


# ---------------------------------------------------------------------------
# list_categories
# ---------------------------------------------------------------------------

def test_list_categories_includes_general():
    assert "general" in list_categories()


def test_list_categories_includes_database():
    assert "database" in list_categories()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("DB_HOST=localhost\nSECRET_KEY=s3cr3t\nAPP_NAME=myapp\n")
    return str(f)


def make_args(tmp_env_file, **kwargs):
    defaults = argparse.Namespace(
        file=tmp_env_file,
        category=None,
        no_mask=False,
        list_categories=False,
    )
    for k, v in kwargs.items():
        setattr(defaults, k, v)
    return defaults


def test_build_parser_returns_parser():
    parser = build_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_classify_exits_zero(tmp_env_file, capsys):
    args = make_args(tmp_env_file)
    assert run_classify(args) == 0


def test_classify_output_contains_category(tmp_env_file, capsys):
    args = make_args(tmp_env_file)
    run_classify(args)
    out = capsys.readouterr().out
    assert "[" in out  # at least one category header


def test_classify_masks_sensitive_by_default(tmp_env_file, capsys):
    args = make_args(tmp_env_file)
    run_classify(args)
    out = capsys.readouterr().out
    assert "s3cr3t" not in out


def test_classify_no_mask_reveals_values(tmp_env_file, capsys):
    args = make_args(tmp_env_file, no_mask=True)
    run_classify(args)
    out = capsys.readouterr().out
    assert "s3cr3t" in out


def test_classify_category_filter(tmp_env_file, capsys):
    args = make_args(tmp_env_file, category="general")
    rc = run_classify(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "[general]" in out


def test_classify_unknown_category_returns_error(tmp_env_file, capsys):
    args = make_args(tmp_env_file, category="nonexistent_cat")
    rc = run_classify(args)
    assert rc == 1


def test_classify_list_categories_flag(tmp_env_file, capsys):
    args = make_args(tmp_env_file, list_categories=True)
    rc = run_classify(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "database" in out
    assert "general" in out


def test_classify_missing_file_returns_error(tmp_path, capsys):
    args = make_args(str(tmp_path / "missing.env"))
    rc = run_classify(args)
    assert rc == 1
