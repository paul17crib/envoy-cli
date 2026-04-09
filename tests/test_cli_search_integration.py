import pytest
import argparse
from io import StringIO
from envoy.cli_search import run_search


@pytest.fixture
def rich_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "APP_NAME=envoy\n"
        "APP_ENV=production\n"
        "DB_HOST=db.internal\n"
        "DB_PASSWORD=s3cr3tpassword\n"
        "REDIS_URL=redis://localhost:6379\n"
        "JWT_SECRET=myjwtsecret\n"
        "LOG_LEVEL=info\n"
    )
    return str(env_file)


def make_args(file, query, **kwargs):
    defaults = {
        "file": file,
        "query": query,
        "keys_only": False,
        "values_only": False,
        "no_mask": False,
        "case_sensitive": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_search_all_app_keys(rich_env_file):
    out = StringIO()
    args = make_args(rich_env_file, "app", keys_only=True)
    result = run_search(args, out=out)
    assert result == 0
    output = out.getvalue()
    assert "APP_NAME" in output
    assert "APP_ENV" in output
    assert "DB_HOST" not in output


def test_search_by_value_substring(rich_env_file):
    out = StringIO()
    args = make_args(rich_env_file, "localhost", values_only=True)
    result = run_search(args, out=out)
    assert result == 0
    output = out.getvalue()
    assert "REDIS_URL" in output
    assert "DB_HOST" not in output


def test_search_sensitive_keys_masked_in_results(rich_env_file):
    out = StringIO()
    args = make_args(rich_env_file, "secret")
    run_search(args, out=out)
    output = out.getvalue()
    assert "myjwtsecret" not in output
    assert "JWT_SECRET" in output


def test_search_unmasked_shows_all_values(rich_env_file):
    out = StringIO()
    args = make_args(rich_env_file, "db", no_mask=True)
    run_search(args, out=out)
    output = out.getvalue()
    assert "s3cr3tpassword" in output
