"""Tests for envoy.cli_zip."""
import pytest
from pathlib import Path
from envoy.cli_zip import run_zip, build_parser
from envoy.sync import save_local


@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def left_file(temp_dir):
    p = temp_dir / "left.env"
    save_local(str(p), {"HOST": "localhost", "PORT": "5432", "DEBUG": "true"}, overwrite=True)
    return str(p)


@pytest.fixture
def right_file(temp_dir):
    p = temp_dir / "right.env"
    save_local(str(p), {"HOST": "remotehost", "PORT": "5433"}, overwrite=True)
    return str(p)


def make_merge_args(left, right, output=None, delimiter="|", keys=None, dry_run=False):
    class Args:
        zip_cmd = "merge"
    a = Args()
    a.left = left
    a.right = right
    a.output = output
    a.delimiter = delimiter
    a.keys = keys
    a.dry_run = dry_run
    return a


def make_split_args(file, left_output=None, right_output=None, delimiter="|", keys=None, list_only=False):
    class Args:
        zip_cmd = "split"
    a = Args()
    a.file = file
    a.left_output = left_output
    a.right_output = right_output
    a.delimiter = delimiter
    a.keys = keys
    a.list_only = list_only
    return a


def test_build_parser_returns_parser():
    parser = build_parser()
    assert parser is not None


def test_merge_writes_output_file(left_file, right_file, temp_dir):
    out = str(temp_dir / "merged.env")
    args = make_merge_args(left_file, right_file, output=out)
    rc = run_zip(args)
    assert rc == 0
    content = Path(out).read_text()
    assert "HOST" in content


def test_merge_dry_run_does_not_write(left_file, right_file, temp_dir, capsys):
    out = str(temp_dir / "merged.env")
    args = make_merge_args(left_file, right_file, output=out, dry_run=True)
    rc = run_zip(args)
    assert rc == 0
    assert not Path(out).exists()
    captured = capsys.readouterr()
    assert "HOST" in captured.out


def test_merge_combines_shared_keys(left_file, right_file, temp_dir, capsys):
    args = make_merge_args(left_file, right_file)
    run_zip(args)
    captured = capsys.readouterr()
    assert "localhost|remotehost" in captured.out


def test_merge_missing_file_returns_error(right_file, capsys):
    args = make_merge_args("/no/such/file.env", right_file)
    rc = run_zip(args)
    assert rc == 1


def test_split_stdout_shows_both_sides(temp_dir, capsys):
    merged = temp_dir / "merged.env"
    save_local(str(merged), {"HOST": "a|b", "PORT": "1|2"}, overwrite=True)
    args = make_split_args(str(merged))
    rc = run_zip(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "LEFT" in out
    assert "RIGHT" in out


def test_split_list_only_shows_zipped_keys(temp_dir, capsys):
    merged = temp_dir / "merged.env"
    save_local(str(merged), {"HOST": "a|b", "DEBUG": "true"}, overwrite=True)
    args = make_split_args(str(merged), list_only=True)
    rc = run_zip(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "HOST" in out
    assert "DEBUG" not in out


def test_split_writes_left_and_right_files(temp_dir):
    merged = temp_dir / "merged.env"
    save_local(str(merged), {"HOST": "a|b"}, overwrite=True)
    left_out = str(temp_dir / "left_out.env")
    right_out = str(temp_dir / "right_out.env")
    args = make_split_args(str(merged), left_output=left_out, right_output=right_out)
    rc = run_zip(args)
    assert rc == 0
    assert Path(left_out).exists()
    assert Path(right_out).exists()
