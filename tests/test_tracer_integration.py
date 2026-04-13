"""Integration tests for the tracer module."""

from __future__ import annotations

from pathlib import Path

import pytest

from envoy.tracer import scan_directory, trace_env, unused_keys, undeclared_refs


@pytest.fixture()
def rich_src(tmp_path: Path) -> tuple[Path, dict]:
    env = {
        "DATABASE_URL": "postgres://localhost/mydb",
        "REDIS_URL": "redis://localhost:6379",
        "SECRET_KEY": "abc123",
        "API_KEY": "xyz",
        "ORPHAN_KEY": "never_used",
    }
    (tmp_path / "db.py").write_text(
        'import os\n'
        'url = os.environ.get("DATABASE_URL")\n'
        'redis = os.getenv("REDIS_URL")\n'
    )
    (tmp_path / "auth.py").write_text(
        'import os\n'
        'secret = os.environ["SECRET_KEY"]\n'
        'api = os.environ.get("API_KEY")\n'
        'external = os.environ.get("EXTERNAL_KEY")\n'
    )
    return tmp_path, env


def test_integration_all_referenced_keys_found(rich_src) -> None:
    src_dir, env = rich_src
    usage = trace_env(env, src_dir, extensions=[".py"])
    assert len(usage["DATABASE_URL"]) >= 1
    assert len(usage["REDIS_URL"]) >= 1
    assert len(usage["SECRET_KEY"]) >= 1
    assert len(usage["API_KEY"]) >= 1


def test_integration_orphan_key_is_unused(rich_src) -> None:
    src_dir, env = rich_src
    result = unused_keys(env, src_dir, extensions=[".py"])
    assert "ORPHAN_KEY" in result
    assert "DATABASE_URL" not in result


def test_integration_external_key_is_undeclared(rich_src) -> None:
    src_dir, env = rich_src
    result = undeclared_refs(env, src_dir, extensions=[".py"])
    assert "EXTERNAL_KEY" in result
    assert "DATABASE_URL" not in result


def test_integration_scan_directory_returns_nonempty(rich_src) -> None:
    src_dir, _ = rich_src
    results = scan_directory(src_dir, extensions=[".py"])
    assert len(results) == 2
    all_keys: set = set()
    for keys in results.values():
        all_keys.update(keys)
    assert "DATABASE_URL" in all_keys
    assert "EXTERNAL_KEY" in all_keys


def test_integration_no_py_files_returns_empty(tmp_path: Path) -> None:
    env = {"KEY": "val"}
    result = trace_env(env, tmp_path, extensions=[".py"])
    assert result == {"KEY": []}
