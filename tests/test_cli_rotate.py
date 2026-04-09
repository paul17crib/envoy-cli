import types
import pytest
from io import StringIO
from pathlib import Path
from envoy.cli_rotate import run_rotate, build_parser


@pytest.fixture
def tmp_env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("SECRET_KEY=abc123\nDB_PASSWORD=hunter2\nAPP_NAME=myapp\n")
    return f


def make_args(file, keys=None, length=32, dry_run=False, backup=False):
    return types.SimpleNamespace(
        file=str(file),
        keys=keys,
        length=length,
        dry_run=dry_run,
        backup=backup,
    )


def test_rotate_replaces_sensitive_keys(tmp_env_file):
    out, err = StringIO(), StringIO()
    args = make_args(tmp_env_file)
    rc = run_rotate(args, out=out, err=err)
    assert rc == 0
    content = tmp_env_file.read_text()
    assert "abc123" not in content
    assert "hunter2" not in content
    assert "APP_NAME=myapp" in content


def test_rotate_dry_run_does_not_write(tmp_env_file):
    original = tmp_env_file.read_text()
    out, err = StringIO(), StringIO()
    args = make_args(tmp_env_file, dry_run=True)
    rc = run_rotate(args, out=out, err=err)
    assert rc == 0
    assert tmp_env_file.read_text() == original
    assert "Dry run" in out.getvalue()


def test_rotate_specific_keys(tmp_env_file):
    out, err = StringIO(), StringIO()
    args = make_args(tmp_env_file, keys=["SECRET_KEY"])
    rc = run_rotate(args, out=out, err=err)
    assert rc == 0
    from envoy.sync import load_local
    env = load_local(str(tmp_env_file))
    assert env["SECRET_KEY"] != "abc123"
    assert env["DB_PASSWORD"] == "hunter2"


def test_rotate_missing_file_returns_error(tmp_path):
    out, err = StringIO(), StringIO()
    args = make_args(tmp_path / "nonexistent.env")
    rc = run_rotate(args, out=out, err=err)
    assert rc == 1
    assert "Error" in err.getvalue()


def test_rotate_no_sensitive_keys(tmp_path):
    f = tmp_path / ".env"
    f.write_text("APP_NAME=myapp\nPORT=8080\n")
    out, err = StringIO(), StringIO()
    args = make_args(f)
    rc = run_rotate(args, out=out, err=err)
    assert rc == 0
    assert "No sensitive" in out.getvalue()


def test_rotate_output_lists_rotated_keys(tmp_env_file):
    out, err = StringIO(), StringIO()
    args = make_args(tmp_env_file, keys=["SECRET_KEY", "DB_PASSWORD"])
    run_rotate(args, out=out, err=err)
    output = out.getvalue()
    assert "SECRET_KEY" in output
    assert "DB_PASSWORD" in output


def test_build_parser_returns_parser():
    parser = build_parser()
    args = parser.parse_args(["--file", ".env", "--dry-run", "--length", "16"])
    assert args.dry_run is True
    assert args.length == 16
