"""Tests for envoy.tracer."""

from __future__ import annotations

from pathlib import Path

import pytest

from envoy.tracer import (
    TracerError,
    scan_file,
    scan_directory,
    trace_env,
    unused_keys,
    undeclared_refs,
)


@pytest.fixture()
def src_dir(tmp_path: Path) -> Path:
    (tmp_path / "app.py").write_text(
        'import os\n'
        'DB = os.environ.get("DATABASE_URL")\n'
        'SECRET = os.environ["SECRET_KEY"]\n'
        'DEBUG = os.getenv("DEBUG")\n'
    )
    (tmp_path / "server.js").write_text(
        'const port = process.env.PORT;\n'
        'const token = process.env.API_TOKEN;\n'
    )
    return tmp_path


def test_scan_file_detects_os_environ_get(tmp_path: Path) -> None:
    f = tmp_path / "mod.py"
    f.write_text('os.environ.get("MY_KEY")')
    assert "MY_KEY" in scan_file(f)


def test_scan_file_detects_os_environ_subscript(tmp_path: Path) -> None:
    f = tmp_path / "mod.py"
    f.write_text('os.environ["ANOTHER_KEY"]')
    assert "ANOTHER_KEY" in scan_file(f)


def test_scan_file_detects_getenv(tmp_path: Path) -> None:
    f = tmp_path / "mod.py"
    f.write_text('os.getenv("LOG_LEVEL")')
    assert "LOG_LEVEL" in scan_file(f)


def test_scan_file_detects_process_env_js(tmp_path: Path) -> None:
    f = tmp_path / "app.js"
    f.write_text("process.env.NODE_ENV")
    assert "NODE_ENV" in scan_file(f)


def test_scan_file_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(TracerError):
        scan_file(tmp_path / "nonexistent.py")


def test_scan_file_empty_returns_empty_set(tmp_path: Path) -> None:
    f = tmp_path / "empty.py"
    f.write_text("")
    assert scan_file(f) == set()


def test_scan_directory_finds_keys_in_multiple_files(src_dir: Path) -> None:
    results = scan_directory(src_dir)
    all_keys: set = set()
    for keys in results.values():
        all_keys.update(keys)
    assert "DATABASE_URL" in all_keys
    assert "SECRET_KEY" in all_keys
    assert "PORT" in all_keys
    assert "API_TOKEN" in all_keys


def test_scan_directory_filters_by_extension(src_dir: Path) -> None:
    results = scan_directory(src_dir, extensions=[".py"])
    all_keys: set = set()
    for keys in results.values():
        all_keys.update(keys)
    assert "DATABASE_URL" in all_keys
    assert "PORT" not in all_keys


def test_trace_env_maps_keys_to_files(src_dir: Path) -> None:
    env = {"DATABASE_URL": "x", "SECRET_KEY": "y", "PORT": "8080"}
    usage = trace_env(env, src_dir)
    assert any("app.py" in f for f in usage["DATABASE_URL"])
    assert any("server.js" in f for f in usage["PORT"])


def test_unused_keys_returns_unreferenced(src_dir: Path) -> None:
    env = {"DATABASE_URL": "x", "UNUSED_KEY": "y"}
    result = unused_keys(env, src_dir)
    assert "UNUSED_KEY" in result
    assert "DATABASE_URL" not in result


def test_undeclared_refs_returns_unknown_keys(src_dir: Path) -> None:
    env = {"DATABASE_URL": "x"}  # missing SECRET_KEY, DEBUG, PORT, API_TOKEN
    result = undeclared_refs(env, src_dir)
    assert "SECRET_KEY" in result
    assert "DATABASE_URL" not in result
