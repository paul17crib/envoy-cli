import pytest
import argparse
from pathlib import Path
from io import StringIO
from envoy.cli_clone import build_parser, run_clone


@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def source_env(temp_dir):
    f = temp_dir / ".env"
    f.write_text("APP_NAME=myapp\nSECRET_KEY=supersecret\nDEBUG=true\nDB_PASSWORD=hunter2\n")
    return f


def make_args(source, destination, keys=None, exclude=None, mask=False, overwrite=False, dry_run=False):
    return argparse.Namespace(
        source=str(source),
        destination=str(destination),
        keys=keys,
        exclude=exclude,
        mask=mask,
        overwrite=overwrite,
        dry_run=dry_run,
    )


def test_clone_copies_all_keys(source_env, temp_dir):
    dest = temp_dir / "clone.env"
    args = make_args(source_env, dest)
    out, err = StringIO(), StringIO()
    rc = run_clone(args, out=out, err=err)
    assert rc == 0
    assert dest.exists()
    content = dest.read_text()
    assert "APP_NAME=myapp" in content
    assert "SECRET_KEY=supersecret" in content


def test_clone_specific_keys(source_env, temp_dir):
    dest = temp_dir / "partial.env"
    args = make_args(source_env, dest, keys=["APP_NAME", "DEBUG"])
    out, err = StringIO(), StringIO()
    rc = run_clone(args, out=out, err=err)
    assert rc == 0
    content = dest.read_text()
    assert "APP_NAME=myapp" in content
    assert "DEBUG=true" in content
    assert "SECRET_KEY" not in content


def test_clone_exclude_keys(source_env, temp_dir):
    dest = temp_dir / "excluded.env"
    args = make_args(source_env, dest, exclude=["SECRET_KEY", "DB_PASSWORD"])
    out, err = StringIO(), StringIO()
    rc = run_clone(args, out=out, err=err)
    assert rc == 0
    content = dest.read_text()
    assert "APP_NAME=myapp" in content
    assert "SECRET_KEY" not in content
    assert "DB_PASSWORD" not in content


def test_clone_missing_source_returns_error(temp_dir):
    dest = temp_dir / "out.env"
    args = make_args(temp_dir / "nonexistent.env", dest)
    out, err = StringIO(), StringIO()
    rc = run_clone(args, out=out, err=err)
    assert rc == 1
    assert "Error" in err.getvalue()


def test_clone_no_overwrite_returns_error(source_env, temp_dir):
    dest = temp_dir / "exists.env"
    dest.write_text("EXISTING=value\n")
    args = make_args(source_env, dest, overwrite=False)
    out, err = StringIO(), StringIO()
    rc = run_clone(args, out=out, err=err)
    assert rc == 1
    assert "Error" in err.getvalue()


def test_clone_overwrite_replaces_file(source_env, temp_dir):
    dest = temp_dir / "exists.env"
    dest.write_text("EXISTING=value\n")
    args = make_args(source_env, dest, overwrite=True)
    out, err = StringIO(), StringIO()
    rc = run_clone(args, out=out, err=err)
    assert rc == 0
    assert "APP_NAME" in dest.read_text()


def test_clone_dry_run_does_not_write(source_env, temp_dir):
    dest = temp_dir / "dryrun.env"
    args = make_args(source_env, dest, dry_run=True)
    out, err = StringIO(), StringIO()
    rc = run_clone(args, out=out, err=err)
    assert rc == 0
    assert not dest.exists()
    assert "APP_NAME=myapp" in out.getvalue()


def test_clone_mask_hides_sensitive_values(source_env, temp_dir):
    dest = temp_dir / "masked.env"
    args = make_args(source_env, dest, mask=True)
    out, err = StringIO(), StringIO()
    rc = run_clone(args, out=out, err=err)
    assert rc == 0
    content = dest.read_text()
    assert "supersecret" not in content
    assert "hunter2" not in content


def test_clone_missing_specific_key_returns_error(source_env, temp_dir):
    dest = temp_dir / "out.env"
    args = make_args(source_env, dest, keys=["NONEXISTENT_KEY"])
    out, err = StringIO(), StringIO()
    rc = run_clone(args, out=out, err=err)
    assert rc == 1
    assert "NONEXISTENT_KEY" in err.getvalue()
