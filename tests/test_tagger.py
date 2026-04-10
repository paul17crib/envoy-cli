"""Tests for envoy/tagger.py and envoy/cli_tag.py."""

import argparse
import pytest
from unittest.mock import patch, MagicMock

from envoy.tagger import (
    parse_tags_from_comment,
    build_tag_comment,
    extract_tags,
    set_tags,
    remove_tags,
    filter_by_tag,
    list_tags,
)
from envoy.cli_tag import build_parser, run_tag


# --- tagger unit tests ---

def test_parse_tags_from_comment_valid():
    result = parse_tags_from_comment("# @tags: prod, secret")
    assert result == ["prod", "secret"]


def test_parse_tags_from_comment_single():
    assert parse_tags_from_comment("# @tags: dev") == ["dev"]


def test_parse_tags_from_comment_invalid_prefix():
    assert parse_tags_from_comment("# not a tag line") == []


def test_build_tag_comment_sorts_tags():
    result = build_tag_comment(["prod", "alpha", "beta"])
    assert result == "# @tags: alpha, beta, prod"


def test_extract_tags_returns_mapping():
    env = {"APP_KEY": "abc", "__tags__APP_KEY": "prod, secret"}
    result = extract_tags(env)
    assert result == {"APP_KEY": ["prod", "secret"]}


def test_extract_tags_empty_env():
    assert extract_tags({}) == {}


def test_set_tags_adds_meta_entry():
    env = {"DB_PASS": "hunter2"}
    updated = set_tags(env, "DB_PASS", ["secret", "prod"])
    assert "__tags__DB_PASS" in updated
    assert "prod" in updated["__tags__DB_PASS"]
    assert "secret" in updated["__tags__DB_PASS"]


def test_set_tags_empty_removes_entry():
    env = {"DB_PASS": "x", "__tags__DB_PASS": "secret"}
    updated = set_tags(env, "DB_PASS", [])
    assert "__tags__DB_PASS" not in updated


def test_remove_tags_clears_entry():
    env = {"KEY": "val", "__tags__KEY": "dev"}
    updated = remove_tags(env, "KEY")
    assert "__tags__KEY" not in updated


def test_filter_by_tag_returns_matching_keys():
    env = {
        "API_KEY": "abc",
        "__tags__API_KEY": "secret, prod",
        "APP_NAME": "myapp",
        "__tags__APP_NAME": "dev",
    }
    result = filter_by_tag(env, "prod")
    assert "API_KEY" in result
    assert "APP_NAME" not in result
    assert "__tags__API_KEY" not in result


def test_filter_by_tag_no_matches():
    env = {"X": "1", "__tags__X": "dev"}
    assert filter_by_tag(env, "prod") == {}


def test_list_tags_returns_sorted_unique():
    env = {
        "__tags__A": "prod, secret",
        "__tags__B": "dev, prod",
    }
    result = list_tags(env)
    assert result == ["dev", "prod", "secret"]


def test_list_tags_empty():
    assert list_tags({}) == []


# --- cli_tag tests ---

def make_args(tag_cmd, **kwargs):
    base = argparse.Namespace(file=".env", tag_cmd=tag_cmd)
    for k, v in kwargs.items():
        setattr(base, k, v)
    return base


def test_run_tag_no_subcommand_returns_error():
    args = make_args(None)
    assert run_tag(args) == 1


def test_run_tag_set(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("API_KEY=secret\n")
    args = make_args("set", key="API_KEY", tags=["prod"], file=str(env_file))
    rc = run_tag(args)
    assert rc == 0
    content = env_file.read_text()
    assert "__tags__API_KEY" in content


def test_run_tag_list(tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text("API_KEY=x\n__tags__API_KEY=prod\n")
    args = make_args("list", file=str(env_file))
    rc = run_tag(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "prod" in out


def test_run_tag_filter(tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text("API_KEY=secret\n__tags__API_KEY=prod\nAPP=myapp\n")
    args = make_args("filter", tag="prod", file=str(env_file))
    rc = run_tag(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "API_KEY" in out
    assert "APP=" not in out


def test_run_tag_show_no_tags(tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\n")
    args = make_args("show", key="FOO", file=str(env_file))
    rc = run_tag(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "no tags" in out


def test_run_tag_missing_file_returns_error(tmp_path):
    args = make_args("list", file=str(tmp_path / "missing.env"))
    assert run_tag(args) == 1
