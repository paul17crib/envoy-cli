"""Tests for envoy.cli_sort2 module."""

import pytest
from pathlib import Path
from envoy.cli_sort2 import build_parser, run_sort2
from envoy.parser import serialize_env


@pytest.fixture
def tmp_env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("ZEBRA=z\nAPP_NAME=myapp\nDB_HOST=localhost\nPORT=8080\n")
    return f


def make_args(file, by="key", reverse=False, case_sensitive=False,
              delimiter="_", dry_run=False, stdout=False):
    parser = build_parser()
    argv = [str(file), "--by", by]
    if reverse:
        argv.append("--reverse")
    if case_sensitive:
        argv.append("--case-sensitive")
    if dry_run:
        argv.append("--dry-run")
    if stdout:
        argv.append("--stdout")
    argv += ["--delimiter", delimiter]
    return parser.parse_args(argv)


def test_sort_by_key_writes_file(tmp_env_file):
    args = make_args(tmp_env_file, by="key")
    rc = run_sort2(args)
    assert rc == 0
    content = tmp_env_file.read_text()
    keys = [line.split("=")[0] for line in content.splitlines() if "=" in line]
    assert keys == sorted(keys, key=str.lower)


def test_sort_reverse_order(tmp_env_file):
    args = make_args(tmp_env_file, by="key", reverse=True)
    rc = run_sort2(args)
    assert rc == 0
    content = tmp_env_file.read_text()
    keys = [line.split("=")[0] for line in content.splitlines() if "=" in line]
    assert keys == sorted(keys, key=str.lower, reverse=True)


def test_sort_by_value(tmp_env_file):
    args = make_args(tmp_env_file, by="value")
    rc = run_sort2(args)
    assert rc == 0
    content = tmp_env_file.read_text()
    assert "=" in content


def test_sort_by_length(tmp_env_file):
    args = make_args(tmp_env_file, by="length")
    rc = run_sort2(args)
    assert rc == 0
    content = tmp_env_file.read_text()
    keys = [line.split("=")[0] for line in content.splitlines() if "=" in line]
    assert keys == sorted(keys, key=len)


def test_sort_by_group(tmp_env_file):
    args = make_args(tmp_env_file, by="group")
    rc = run_sort2(args)
    assert rc == 0


def test_dry_run_does_not_modify_file(tmp_env_file):
    original = tmp_env_file.read_text()
    args = make_args(tmp_env_file, dry_run=True)
    rc = run_sort2(args)
    assert rc == 0
    assert tmp_env_file.read_text() == original


def test_stdout_does_not_modify_file(tmp_env_file, capsys):
    original = tmp_env_file.read_text()
    args = make_args(tmp_env_file, stdout=True)
    rc = run_sort2(args)
    assert rc == 0
    assert tmp_env_file.read_text() == original
    captured = capsys.readouterr()
    assert "=" in captured.out


def test_missing_file_returns_error(tmp_path):
    args = make_args(tmp_path / "missing.env")
    rc = run_sort2(args)
    assert rc == 1


def test_build_parser_returns_parser():
    parser = build_parser()
    assert parser is not None


def test_sort_preserves_all_keys(tmp_env_file):
    original_env = {}
    for line in tmp_env_file.read_text().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            original_env[k] = v

    args = make_args(tmp_env_file, by="key")
    run_sort2(args)

    result_env = {}
    for line in tmp_env_file.read_text().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            result_env[k] = v

    assert set(result_env.keys()) == set(original_env.keys())
