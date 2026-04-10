import pytest
import argparse
from io import StringIO
from pathlib import Path
from envoy.cli_clone import run_clone
from envoy.sync import load_local


@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def rich_env_file(temp_dir):
    f = temp_dir / ".env"
    f.write_text(
        "APP_NAME=envoy\n"
        "APP_ENV=production\n"
        "SECRET_KEY=abc123xyz\n"
        "DB_PASSWORD=s3cr3t!\n"
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "API_TOKEN=tok_live_abcdef\n"
        "DEBUG=false\n"
    )
    return f


def make_args(source, destination, **kwargs):
    defaults = dict(keys=None, exclude=None, mask=False, overwrite=False, dry_run=False)
    defaults.update(kwargs)
    return argparse.Namespace(source=str(source), destination=str(destination), **defaults)


def test_integration_clone_preserves_all_keys(rich_env_file, temp_dir):
    dest = temp_dir / "full_clone.env"
    args = make_args(rich_env_file, dest)
    rc = run_clone(args, out=StringIO(), err=StringIO())
    assert rc == 0
    cloned = load_local(dest)
    original = load_local(rich_env_file)
    assert cloned == original


def test_integration_exclude_then_verify_remaining(rich_env_file, temp_dir):
    dest = temp_dir / "no_db.env"
    args = make_args(rich_env_file, dest, exclude=["DB_PASSWORD", "DB_HOST", "DB_PORT"])
    rc = run_clone(args, out=StringIO(), err=StringIO())
    assert rc == 0
    cloned = load_local(dest)
    assert "DB_PASSWORD" not in cloned
    assert "DB_HOST" not in cloned
    assert "APP_NAME" in cloned
    assert "SECRET_KEY" in cloned


def test_integration_masked_clone_values_replaced(rich_env_file, temp_dir):
    dest = temp_dir / "masked.env"
    args = make_args(rich_env_file, dest, mask=True)
    rc = run_clone(args, out=StringIO(), err=StringIO())
    assert rc == 0
    cloned = load_local(dest)
    assert cloned["SECRET_KEY"] != "abc123xyz"
    assert cloned["DB_PASSWORD"] != "s3cr3t!"
    assert cloned["APP_NAME"] == "envoy"


def test_integration_dry_run_output_matches_expected_keys(rich_env_file, temp_dir):
    dest = temp_dir / "never_written.env"
    out = StringIO()
    args = make_args(rich_env_file, dest, keys=["APP_NAME", "APP_ENV"], dry_run=True)
    rc = run_clone(args, out=out, err=StringIO())
    assert rc == 0
    assert not dest.exists()
    output = out.getvalue()
    assert "APP_NAME=envoy" in output
    assert "APP_ENV=production" in output
    assert "SECRET_KEY" not in output
