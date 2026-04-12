"""Integration tests for pin workflow: add -> drift -> remove."""

import argparse
import json
from pathlib import Path

import pytest

from envoy.cli_pin import run_pin


@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def rich_env_file(temp_dir):
    content = (
        "DB_HOST=prod.db.example.com\n"
        "DB_PORT=5432\n"
        "API_KEY=s3cr3t_k3y_xyz\n"
        "APP_ENV=production\n"
        "CACHE_TTL=300\n"
    )
    p = temp_dir / ".env"
    p.write_text(content, encoding="utf-8")
    return str(p)


def make_args(**kwargs):
    defaults = {"action": "add", "keys": [], "file": ".env", "pin_file": ".env.pins", "no_mask": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_integration_full_workflow(rich_env_file, temp_dir):
    pin_file = str(temp_dir / ".env.pins")

    # Pin several keys
    rc = run_pin(make_args(action="add", keys=["DB_HOST", "APP_ENV", "CACHE_TTL"],
                           file=rich_env_file, pin_file=pin_file))
    assert rc == 0

    # Check — no drift yet
    rc = run_pin(make_args(action="check", file=rich_env_file, pin_file=pin_file))
    assert rc == 0

    # Modify the env file to introduce drift
    env_path = Path(rich_env_file)
    env_path.write_text(env_path.read_text().replace("prod.db.example.com", "staging.db.example.com"))

    # Check — drift expected on DB_HOST
    rc = run_pin(make_args(action="check", file=rich_env_file, pin_file=pin_file))
    assert rc == 1

    # Remove the drifted pin
    rc = run_pin(make_args(action="remove", keys=["DB_HOST"], pin_file=pin_file))
    assert rc == 0

    # Check again — drift resolved
    rc = run_pin(make_args(action="check", file=rich_env_file, pin_file=pin_file))
    assert rc == 0


def test_integration_pinned_values_persisted(rich_env_file, temp_dir):
    pin_file = str(temp_dir / "custom.pins")
    run_pin(make_args(action="add", keys=["DB_PORT", "CACHE_TTL"],
                      file=rich_env_file, pin_file=pin_file))
    pins = json.loads(Path(pin_file).read_text())
    assert pins["DB_PORT"] == "5432"
    assert pins["CACHE_TTL"] == "300"


def test_integration_masked_output_on_drift(rich_env_file, temp_dir, capsys):
    pin_file = str(temp_dir / ".env.pins")
    run_pin(make_args(action="add", keys=["API_KEY"], file=rich_env_file, pin_file=pin_file))

    # Change the API_KEY in env
    env_path = Path(rich_env_file)
    env_path.write_text(env_path.read_text().replace("s3cr3t_k3y_xyz", "new_secret_value"))

    rc = run_pin(make_args(action="check", file=rich_env_file, pin_file=pin_file, no_mask=False))
    assert rc == 1
    out = capsys.readouterr().out
    # Masked output should not reveal the raw secret
    assert "new_secret_value" not in out
