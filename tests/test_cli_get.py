import argparse
import io
import pytest

from envoy.cli_get import build_parser, run_get
from envoy.sync import save_local


@pytest.fixture
def tmp_env_file(tmp_path):
    path = tmp_path / ".env"
    save_local(
        {
            "APP_NAME": "myapp",
            "SECRET_KEY": "supersecret",
            "DATABASE_URL": "postgres://localhost/db",
            "DEBUG": "true",
        },
        str(path),
    )
    return str(path)


def make_args(keys, file, no_mask=False, export=False, quiet=False):
    return argparse.Namespace(
        keys=keys,
        file=file,
        no_mask=no_mask,
        export=export,
        quiet=quiet,
    )


def test_get_single_key(tmp_env_file):
    out = io.StringIO()
    args = make_args(["APP_NAME"], tmp_env_file)
    result = run_get(args, out=out)
    assert result == 0
    assert "APP_NAME=myapp" in out.getvalue()


def test_get_multiple_keys(tmp_env_file):
    out = io.StringIO()
    args = make_args(["APP_NAME", "DEBUG"], tmp_env_file)
    result = run_get(args, out=out)
    assert result == 0
    output = out.getvalue()
    assert "APP_NAME=myapp" in output
    assert "DEBUG=true" in output


def test_get_masks_sensitive_value_by_default(tmp_env_file):
    out = io.StringIO()
    args = make_args(["SECRET_KEY"], tmp_env_file)
    result = run_get(args, out=out)
    assert result == 0
    assert "***" in out.getvalue()
    assert "supersecret" not in out.getvalue()


def test_get_no_mask_reveals_sensitive_value(tmp_env_file):
    out = io.StringIO()
    args = make_args(["SECRET_KEY"], tmp_env_file, no_mask=True)
    result = run_get(args, out=out)
    assert result == 0
    assert "supersecret" in out.getvalue()


def test_get_export_format(tmp_env_file):
    out = io.StringIO()
    args = make_args(["APP_NAME"], tmp_env_file, export=True)
    result = run_get(args, out=out)
    assert result == 0
    assert out.getvalue().strip() == "export APP_NAME=myapp"


def test_get_quiet_mode(tmp_env_file):
    out = io.StringIO()
    args = make_args(["APP_NAME"], tmp_env_file, quiet=True)
    result = run_get(args, out=out)
    assert result == 0
    assert out.getvalue().strip() == "myapp"


def test_get_quiet_mode_multiple_keys(tmp_env_file):
    """Quiet mode with multiple keys should print one value per line."""
    out = io.StringIO()
    args = make_args(["APP_NAME", "DEBUG"], tmp_env_file, quiet=True)
    result = run_get(args, out=out)
    assert result == 0
    lines = out.getvalue().strip().splitlines()
    assert "myapp" in lines
    assert "true" in lines


def test_get_missing_key_returns_error(tmp_env_file):
    out = io.StringIO()
    args = make_args(["NONEXISTENT"], tmp_env_file)
    result = run_get(args, out=out)
    assert result == 1


def test_get_missing_file_returns_error(tmp_path):
    out = io.StringIO()
    args = make_args(["APP_NAME"], str(tmp_path / "missing.env"))
    result = run_get(args, out=out)
    assert result == 1


def test_build_parser_returns_parser():
    parser = build_parser()
    args = parser.parse_args(["MY_KEY", "--file", ".env", "--no-mask"])
    assert args.keys == ["MY_KEY"]
    assert args.file == ".env"
    assert args.no_mask is True
