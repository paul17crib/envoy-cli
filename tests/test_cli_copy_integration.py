import argparse
import pytest
from io import StringIO
from pathlib import Path

from envoy.cli_copy import run_copy
from envoy.sync import save_local, load_local


@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path


def make_args(temp_dir, **kwargs):
    defaults = {
        "source": str(temp_dir / "source.env"),
        "destination": str(temp_dir / "dest.env"),
        "keys": None,
        "overwrite": False,
        "create": True,
        "dry_run": False,
        "no_mask": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_copy_merges_without_losing_dest_keys(temp_dir):
    save_local(str(temp_dir / "source.env"), {"NEW_KEY": "value1", "SHARED": "from_source"})
    save_local(str(temp_dir / "dest.env"), {"EXISTING": "stays", "SHARED": "from_dest"})
    args = make_args(temp_dir)
    out = StringIO()
    result = run_copy(args, out=out)
    assert result == 0
    merged = load_local(args.destination)
    assert merged["EXISTING"] == "stays"
    assert merged["NEW_KEY"] == "value1"
    assert merged["SHARED"] == "from_dest"  # not overwritten


def test_copy_overwrite_replaces_shared_keys(temp_dir):
    save_local(str(temp_dir / "source.env"), {"SHARED": "new_value", "EXTRA": "extra"})
    save_local(str(temp_dir / "dest.env"), {"SHARED": "old_value", "LOCAL": "local"})
    args = make_args(temp_dir, overwrite=True)
    out = StringIO()
    result = run_copy(args, out=out)
    assert result == 0
    merged = load_local(args.destination)
    assert merged["SHARED"] == "new_value"
    assert merged["LOCAL"] == "local"
    assert merged["EXTRA"] == "extra"


def test_copy_subset_of_keys_integration(temp_dir):
    save_local(
        str(temp_dir / "source.env"),
        {"DB_HOST": "localhost", "DB_PASS": "secret", "APP_PORT": "8080"},
    )
    save_local(str(temp_dir / "dest.env"), {"APP_PORT": "9000"})
    args = make_args(temp_dir, keys=["DB_HOST"], overwrite=True)
    out = StringIO()
    result = run_copy(args, out=out)
    assert result == 0
    merged = load_local(args.destination)
    assert merged["DB_HOST"] == "localhost"
    assert "DB_PASS" not in merged
    assert merged["APP_PORT"] == "9000"
