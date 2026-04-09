import argparse
import io
import pytest

from envoy.cli_sort import build_parser, run_sort


@pytest.fixture
def tmp_env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("ZEBRA=1\nAPPLE=2\nMIDDLE=3\n")
    return f


def make_args(file, reverse=False, dry_run=False, stdout=False):
    return argparse.Namespace(
        file=str(file),
        reverse=reverse,
        dry_run=dry_run,
        stdout=stdout,
    )


def test_sort_writes_sorted_file(tmp_env_file):
    args = make_args(tmp_env_file)
    out = io.StringIO()
    result = run_sort(args, out=out)
    assert result == 0
    content = tmp_env_file.read_text()
    keys = [line.split("=")[0] for line in content.strip().splitlines() if "=" in line]
    assert keys == sorted(keys)


def test_sort_reverse_order(tmp_env_file):
    args = make_args(tmp_env_file, reverse=True)
    out = io.StringIO()
    result = run_sort(args, out=out)
    assert result == 0
    content = tmp_env_file.read_text()
    keys = [line.split("=")[0] for line in content.strip().splitlines() if "=" in line]
    assert keys == sorted(keys, reverse=True)


def test_sort_dry_run_does_not_modify_file(tmp_env_file):
    original = tmp_env_file.read_text()
    args = make_args(tmp_env_file, dry_run=True)
    out = io.StringIO()
    result = run_sort(args, out=out)
    assert result == 0
    assert tmp_env_file.read_text() == original
    assert "dry-run" in out.getvalue()


def test_sort_stdout_does_not_modify_file(tmp_env_file):
    original = tmp_env_file.read_text()
    args = make_args(tmp_env_file, stdout=True)
    out = io.StringIO()
    result = run_sort(args, out=out)
    assert result == 0
    assert tmp_env_file.read_text() == original
    output = out.getvalue()
    assert "APPLE" in output
    assert "ZEBRA" in output


def test_sort_missing_file_returns_error(tmp_path):
    args = make_args(tmp_path / "missing.env")
    out = io.StringIO()
    result = run_sort(args, out=out)
    assert result == 1


def test_sort_stdout_output_is_sorted(tmp_env_file):
    args = make_args(tmp_env_file, stdout=True)
    out = io.StringIO()
    run_sort(args, out=out)
    lines = [l for l in out.getvalue().strip().splitlines() if "=" in l]
    keys = [l.split("=")[0] for l in lines]
    assert keys == sorted(keys)


def test_build_parser_returns_parser():
    parser = build_parser()
    args = parser.parse_args([".env", "--reverse"])
    assert args.reverse is True
    assert args.file == ".env"
