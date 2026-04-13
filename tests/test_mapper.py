"""Tests for envoy.mapper and envoy.cli_map."""

from __future__ import annotations

import argparse
import pytest

from envoy.mapper import (
    MapperError,
    build_key_map,
    find_duplicates,
    find_unique,
    format_map_report,
    keys_in_all,
)
from envoy.cli_map import build_parser, run_map


@pytest.fixture()
def two_env_files(tmp_path):
    f1 = tmp_path / "a.env"
    f1.write_text("APP_NAME=alpha\nDB_HOST=localhost\n")
    f2 = tmp_path / "b.env"
    f2.write_text("APP_NAME=beta\nAPI_KEY=secret\n")
    return str(f1), str(f2)


def test_build_key_map_collects_all_keys(two_env_files):
    f1, f2 = two_env_files
    key_map = build_key_map([f1, f2])
    assert set(key_map.keys()) == {"APP_NAME", "DB_HOST", "API_KEY"}


def test_build_key_map_duplicate_has_two_entries(two_env_files):
    f1, f2 = two_env_files
    key_map = build_key_map([f1, f2])
    assert len(key_map["APP_NAME"]) == 2


def test_build_key_map_unique_has_one_entry(two_env_files):
    f1, f2 = two_env_files
    key_map = build_key_map([f1, f2])
    assert len(key_map["DB_HOST"]) == 1
    assert key_map["DB_HOST"][0].value == "localhost"


def test_build_key_map_missing_file_raises(tmp_path):
    with pytest.raises(MapperError, match="not found"):
        build_key_map([str(tmp_path / "missing.env")])


def test_find_duplicates_returns_shared_keys(two_env_files):
    f1, f2 = two_env_files
    key_map = build_key_map([f1, f2])
    dups = find_duplicates(key_map)
    assert "APP_NAME" in dups
    assert "DB_HOST" not in dups


def test_find_unique_returns_single_file_keys(two_env_files):
    f1, f2 = two_env_files
    key_map = build_key_map([f1, f2])
    unique = find_unique(key_map)
    assert "DB_HOST" in unique
    assert "API_KEY" in unique
    assert "APP_NAME" not in unique


def test_keys_in_all_returns_shared_keys(two_env_files):
    f1, f2 = two_env_files
    key_map = build_key_map([f1, f2])
    shared = keys_in_all(key_map, 2)
    assert shared == ["APP_NAME"]


def test_format_map_report_contains_key(two_env_files):
    f1, f2 = two_env_files
    key_map = build_key_map([f1, f2])
    report = format_map_report(key_map)
    assert "APP_NAME" in report


def test_format_map_report_with_values(two_env_files):
    f1, f2 = two_env_files
    key_map = build_key_map([f1, f2])
    report = format_map_report(key_map, show_values=True)
    assert "localhost" in report


def test_run_map_returns_zero(two_env_files, capsys):
    f1, f2 = two_env_files
    parser = build_parser()
    args = parser.parse_args([f1, f2])
    rc = run_map(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "APP_NAME" in out


def test_run_map_duplicates_flag(two_env_files, capsys):
    f1, f2 = two_env_files
    parser = build_parser()
    args = parser.parse_args(["--duplicates", f1, f2])
    rc = run_map(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "APP_NAME" in out
    assert "DB_HOST" not in out


def test_run_map_missing_file_returns_error(tmp_path, capsys):
    parser = build_parser()
    args = parser.parse_args([str(tmp_path / "nope.env")])
    rc = run_map(args)
    assert rc == 1
    assert "error" in capsys.readouterr().err
