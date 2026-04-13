"""Tests for envoy.linker and envoy.cli_link."""

from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

import pytest

from envoy.linker import (
    LinkerError,
    apply_links,
    build_link_map,
    get_linked_keys,
    parse_link_file,
)
from envoy.cli_link import build_parser, run_link


# ---------------------------------------------------------------------------
# build_link_map
# ---------------------------------------------------------------------------

def test_build_link_map_basic():
    lm = build_link_map([("A", "B"), ("C", "D")])
    assert lm == {"A": "B", "C": "D"}


def test_build_link_map_duplicate_source_raises():
    with pytest.raises(LinkerError, match="Duplicate source key"):
        build_link_map([("A", "B"), ("A", "C")])


# ---------------------------------------------------------------------------
# parse_link_file
# ---------------------------------------------------------------------------

def test_parse_link_file_valid():
    text = textwrap.dedent("""\
        # comment
        DB_HOST -> DATABASE_HOST
        DB_PORT -> DATABASE_PORT
    """)
    lm = parse_link_file(text)
    assert lm == {"DB_HOST": "DATABASE_HOST", "DB_PORT": "DATABASE_PORT"}


def test_parse_link_file_skips_blank_lines():
    lm = parse_link_file("\n\nA -> B\n\n")
    assert lm == {"A": "B"}


def test_parse_link_file_malformed_raises():
    with pytest.raises(LinkerError, match="expected 'SRC -> DST'"):
        parse_link_file("BADLINE")


def test_parse_link_file_empty_key_raises():
    with pytest.raises(LinkerError, match="empty key"):
        parse_link_file(" -> DEST")


# ---------------------------------------------------------------------------
# apply_links
# ---------------------------------------------------------------------------

def test_apply_links_copies_value():
    env = {"A": "hello"}
    result = apply_links(env, {"A": "B"})
    assert result["B"] == "hello"
    assert result["A"] == "hello"  # original preserved


def test_apply_links_no_overwrite_skips_existing():
    env = {"A": "new", "B": "existing"}
    result = apply_links(env, {"A": "B"}, overwrite=False)
    assert result["B"] == "existing"


def test_apply_links_overwrite_replaces_existing():
    env = {"A": "new", "B": "existing"}
    result = apply_links(env, {"A": "B"}, overwrite=True)
    assert result["B"] == "new"


def test_apply_links_missing_source_raises():
    with pytest.raises(LinkerError, match="Source key not found"):
        apply_links({}, {"MISSING": "DEST"})


def test_apply_links_does_not_mutate_original():
    env = {"A": "val"}
    apply_links(env, {"A": "B"})
    assert "B" not in env


# ---------------------------------------------------------------------------
# get_linked_keys
# ---------------------------------------------------------------------------

def test_get_linked_keys_returns_destinations():
    env = {"A": "1", "C": "3"}
    keys = get_linked_keys(env, {"A": "B", "C": "D", "MISSING": "X"})
    assert set(keys) == {"B", "D"}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@pytest.fixture()
def temp_dir(tmp_path):
    return tmp_path


def make_args(env_file, link_file, overwrite=False, dry_run=False, stdout=False):
    return argparse.Namespace(
        env_file=str(env_file),
        link_file=str(link_file),
        overwrite=overwrite,
        dry_run=dry_run,
        stdout=stdout,
    )


def test_run_link_writes_linked_keys(temp_dir):
    env_file = temp_dir / ".env"
    env_file.write_text("DB_HOST=localhost\nDB_PORT=5432\n")
    link_file = temp_dir / "links.map"
    link_file.write_text("DB_HOST -> DATABASE_HOST\n")

    rc = run_link(make_args(env_file, link_file))
    assert rc == 0
    content = env_file.read_text()
    assert "DATABASE_HOST=localhost" in content


def test_run_link_dry_run_does_not_write(temp_dir):
    env_file = temp_dir / ".env"
    env_file.write_text("X=42\n")
    link_file = temp_dir / "links.map"
    link_file.write_text("X -> Y\n")
    original = env_file.read_text()

    rc = run_link(make_args(env_file, link_file, dry_run=True))
    assert rc == 0
    assert env_file.read_text() == original


def test_run_link_missing_env_file_returns_error(temp_dir):
    link_file = temp_dir / "links.map"
    link_file.write_text("A -> B\n")
    rc = run_link(make_args(temp_dir / "nonexistent.env", link_file))
    assert rc == 1


def test_run_link_missing_link_file_returns_error(temp_dir):
    env_file = temp_dir / ".env"
    env_file.write_text("A=1\n")
    rc = run_link(make_args(env_file, temp_dir / "no.map"))
    assert rc == 1


def test_build_parser_returns_parser():
    parser = build_parser()
    assert isinstance(parser, argparse.ArgumentParser)
