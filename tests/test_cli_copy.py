import argparse
import pytest
from io import StringIO
from pathlib import Path

from envoy.cli_copy import build_parser, run_copy
from envoy.sync import save_local


@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path


def make_args(temp_dir, **kwargs):
    source = str(temp_dir / "source.env")
    destination = str(temp_dir / "dest.env")
    defaults = {
        "source": source,
        "destination": destination,
        "keys": None,
        "overwrite": False,
        "create": False,
        "dry_run": False,
        "no_mask": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_copy_all_keys_to_new_file(temp_dir):
    save_local(str(temp_dir / "source.env"), {"FOO": "bar", "BAZ": "qux"})
    args = make_args(temp_dir, create=True)
    out = StringIO()
    result = run_copy(args, out=out)
    assert result == 0
    dest = Path(args.destination)
    assert dest.exists()
    content = dest.read_text()
    assert "FOO=bar" in content
    assert "BAZ=qux" in content


def test_copy_specific_keys(temp_dir):
    save_local(str(temp_dir / "source.env"), {"FOO": "bar", "BAZ": "qux", "KEEP": "me"})
    save_local(str(temp_dir / "dest.env"), {})
    args = make_args(temp_dir, keys=["FOO", "KEEP"])
    out = StringIO()
    result = run_copy(args, out=out)
    assert result == 0
    content = Path(args.destination).read_text()
    assert "FOO=bar" in content
    assert "KEEP=me" in content
    assert "BAZ" not in content


def test_copy_missing_source_returns_error(temp_dir):
    args = make_args(temp_dir)
    out = StringIO()
    result = run_copy(args, out=out)
    assert result == 1


def test_copy_missing_destination_without_create_returns_error(temp_dir):
    save_local(str(temp_dir / "source.env"), {"FOO": "bar"})
    args = make_args(temp_dir)
    out = StringIO()
    result = run_copy(args, out=out)
    assert result == 1


def test_copy_does_not_overwrite_existing_key_by_default(temp_dir):
    save_local(str(temp_dir / "source.env"), {"FOO": "new"})
    save_local(str(temp_dir / "dest.env"), {"FOO": "old"})
    args = make_args(temp_dir)
    out = StringIO()
    result = run_copy(args, out=out)
    assert result == 0
    content = Path(args.destination).read_text()
    assert "FOO=old" in content
    assert "Skipped" in out.getvalue()


def test_copy_overwrites_with_flag(temp_dir):
    save_local(str(temp_dir / "source.env"), {"FOO": "new"})
    save_local(str(temp_dir / "dest.env"), {"FOO": "old"})
    args = make_args(temp_dir, overwrite=True)
    out = StringIO()
    result = run_copy(args, out=out)
    assert result == 0
    content = Path(args.destination).read_text()
    assert "FOO=new" in content


def test_copy_dry_run_does_not_write(temp_dir):
    save_local(str(temp_dir / "source.env"), {"FOO": "bar"})
    args = make_args(temp_dir, create=True, dry_run=True)
    out = StringIO()
    result = run_copy(args, out=out)
    assert result == 0
    assert not Path(args.destination).exists()
    assert "Dry run" in out.getvalue()


def test_copy_dry_run_masks_sensitive_values(temp_dir):
    save_local(str(temp_dir / "source.env"), {"SECRET_KEY": "supersecret"})
    args = make_args(temp_dir, create=True, dry_run=True)
    out = StringIO()
    result = run_copy(args, out=out)
    assert result == 0
    assert "supersecret" not in out.getvalue()


def test_copy_missing_specific_key_returns_error(temp_dir):
    save_local(str(temp_dir / "source.env"), {"FOO": "bar"})
    save_local(str(temp_dir / "dest.env"), {})
    args = make_args(temp_dir, keys=["MISSING"])
    out = StringIO()
    result = run_copy(args, out=out)
    assert result == 1


def test_build_parser_returns_parser():
    parser = build_parser()
    assert parser is not None
    args = parser.parse_args(["src.env", "dst.env", "--keys", "FOO", "--overwrite", "--dry-run"])
    assert args.source == "src.env"
    assert args.destination == "dst.env"
    assert args.keys == ["FOO"]
    assert args.overwrite is True
    assert args.dry_run is True
