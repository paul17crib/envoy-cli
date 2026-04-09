import argparse
import io
import pytest

from envoy.cli_sort import run_sort


@pytest.fixture
def complex_env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text(
        "ZEBRA_HOST=localhost\n"
        "APP_NAME=myapp\n"
        "DATABASE_URL=postgres://localhost/db\n"
        "API_KEY=supersecret\n"
        "LOG_LEVEL=info\n"
    )
    return f


def make_args(file, reverse=False, dry_run=False, stdout=False):
    return argparse.Namespace(
        file=str(file),
        reverse=reverse,
        dry_run=dry_run,
        stdout=stdout,
    )


def test_integration_sort_preserves_all_keys(complex_env_file):
    original_keys = {"ZEBRA_HOST", "APP_NAME", "DATABASE_URL", "API_KEY", "LOG_LEVEL"}
    args = make_args(complex_env_file)
    out = io.StringIO()
    result = run_sort(args, out=out)
    assert result == 0
    content = complex_env_file.read_text()
    found_keys = {
        line.split("=")[0]
        for line in content.strip().splitlines()
        if "=" in line
    }
    assert found_keys == original_keys


def test_integration_sort_ascending_then_descending(complex_env_file):
    args_asc = make_args(complex_env_file)
    run_sort(args_asc, out=io.StringIO())
    content_asc = complex_env_file.read_text()
    keys_asc = [l.split("=")[0] for l in content_asc.strip().splitlines() if "=" in l]

    args_desc = make_args(complex_env_file, reverse=True)
    run_sort(args_desc, out=io.StringIO())
    content_desc = complex_env_file.read_text()
    keys_desc = [l.split("=")[0] for l in content_desc.strip().splitlines() if "=" in l]

    assert keys_asc == list(reversed(keys_desc))


def test_integration_dry_run_stdout_match(complex_env_file):
    out_dry = io.StringIO()
    out_stdout = io.StringIO()

    args_dry = make_args(complex_env_file, dry_run=True)
    args_out = make_args(complex_env_file, stdout=True)

    run_sort(args_dry, out=out_dry)
    run_sort(args_out, out=out_stdout)

    dry_lines = [l for l in out_dry.getvalue().splitlines() if "=" in l]
    stdout_lines = [l for l in out_stdout.getvalue().splitlines() if "=" in l]
    assert dry_lines == stdout_lines
