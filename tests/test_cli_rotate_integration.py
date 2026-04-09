import types
import pytest
from io import StringIO
from envoy.cli_rotate import run_rotate
from envoy.sync import load_local
from envoy.rotator import generate_secret


@pytest.fixture
def rich_env_file(tmp_path):
    content = (
        "# Application settings\n"
        "APP_NAME=envoy\n"
        "APP_ENV=production\n"
        "\n"
        "# Secrets\n"
        "SECRET_KEY=supersecret\n"
        "API_TOKEN=tok_abc123\n"
        "DB_PASSWORD=dbpass\n"
    )
    f = tmp_path / ".env"
    f.write_text(content)
    return f


def make_args(file, **kwargs):
    defaults = dict(keys=None, length=32, dry_run=False, backup=False)
    defaults.update(kwargs)
    return types.SimpleNamespace(file=str(file), **defaults)


def test_integration_all_sensitive_keys_rotated(rich_env_file):
    out, err = StringIO(), StringIO()
    run_rotate(make_args(rich_env_file), out=out, err=err)
    env = load_local(str(rich_env_file))
    assert env["SECRET_KEY"] != "supersecret"
    assert env["API_TOKEN"] != "tok_abc123"
    assert env["DB_PASSWORD"] != "dbpass"
    assert env["APP_NAME"] == "envoy"
    assert env["APP_ENV"] == "production"


def test_integration_rotated_values_have_correct_length(rich_env_file):
    run_rotate(make_args(rich_env_file, length=48), out=StringIO(), err=StringIO())
    env = load_local(str(rich_env_file))
    assert len(env["SECRET_KEY"]) == 48


def test_integration_dry_run_preserves_all_values(rich_env_file):
    original = load_local(str(rich_env_file))
    run_rotate(make_args(rich_env_file, dry_run=True), out=StringIO(), err=StringIO())
    after = load_local(str(rich_env_file))
    assert original == after
