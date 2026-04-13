"""Tests for envoy/renamer_bulk.py and envoy/cli_rename_bulk.py."""

from __future__ import annotations

import argparse
import json
import os

import pytest

from envoy.renamer_bulk import (
    BulkRenameError,
    get_rename_preview,
    rename_by_mapping,
    rename_prefix,
)
from envoy.cli_rename_bulk import build_parser, run_rename_bulk


# ---------------------------------------------------------------------------
# renamer_bulk unit tests
# ---------------------------------------------------------------------------

def test_rename_by_mapping_basic():
    env = {"FOO": "1", "BAR": "2"}
    result = rename_by_mapping(env, {"FOO": "FOO_NEW"})
    assert "FOO_NEW" in result
    assert "FOO" not in result
    assert result["BAR"] == "2"


def test_rename_by_mapping_missing_source_skipped():
    env = {"A": "1"}
    result = rename_by_mapping(env, {"MISSING": "X"})
    assert result == {"A": "1"}


def test_rename_by_mapping_conflict_raises():
    env = {"A": "1", "B": "2"}
    with pytest.raises(BulkRenameError):
        rename_by_mapping(env, {"A": "B"})


def test_rename_by_mapping_conflict_overwrite():
    env = {"A": "1", "B": "2"}
    result = rename_by_mapping(env, {"A": "B"}, overwrite=True)
    assert result["B"] == "1"
    assert "A" not in result


def test_rename_prefix_replaces_matching_keys():
    env = {"DB_HOST": "localhost", "DB_PORT": "5432", "APP_NAME": "myapp"}
    result = rename_prefix(env, "DB_", "DATABASE_")
    assert "DATABASE_HOST" in result
    assert "DATABASE_PORT" in result
    assert "APP_NAME" in result
    assert "DB_HOST" not in result


def test_rename_prefix_empty_raises():
    with pytest.raises(BulkRenameError):
        rename_prefix({"A": "1"}, "", "NEW_")


def test_get_rename_preview_excludes_missing():
    env = {"A": "1", "B": "2"}
    preview = get_rename_preview(env, {"A": "Z", "MISSING": "X"})
    assert preview == {"A": "Z"}


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_env_file(tmp_path):
    path = tmp_path / ".env"
    path.write_text("DB_HOST=localhost\nDB_PORT=5432\nAPP_NAME=myapp\n")
    return str(path)


def make_args(file, prefix=None, mapping=None, overwrite=False, dry_run=False):
    ns = argparse.Namespace(
        file=file,
        prefix=prefix,
        mapping=mapping,
        overwrite=overwrite,
        dry_run=dry_run,
    )
    return ns


def test_cli_rename_prefix_writes_file(tmp_env_file):
    args = make_args(tmp_env_file, prefix=["DB_", "DATABASE_"])
    rc = run_rename_bulk(args)
    assert rc == 0
    content = open(tmp_env_file).read()
    assert "DATABASE_HOST" in content
    assert "DB_HOST" not in content


def test_cli_rename_mapping_writes_file(tmp_env_file):
    args = make_args(tmp_env_file, mapping=json.dumps({"APP_NAME": "APPLICATION_NAME"}))
    rc = run_rename_bulk(args)
    assert rc == 0
    content = open(tmp_env_file).read()
    assert "APPLICATION_NAME" in content


def test_cli_dry_run_does_not_write(tmp_env_file):
    original = open(tmp_env_file).read()
    args = make_args(tmp_env_file, prefix=["DB_", "X_"], dry_run=True)
    rc = run_rename_bulk(args)
    assert rc == 0
    assert open(tmp_env_file).read() == original


def test_cli_invalid_json_returns_error(tmp_env_file):
    args = make_args(tmp_env_file, mapping="{not valid json}")
    rc = run_rename_bulk(args)
    assert rc == 1


def test_cli_missing_file_returns_error(tmp_path):
    args = make_args(str(tmp_path / "nonexistent.env"), prefix=["A_", "B_"])
    rc = run_rename_bulk(args)
    assert rc == 1


def test_build_parser_returns_parser():
    p = build_parser()
    assert isinstance(p, argparse.ArgumentParser)
