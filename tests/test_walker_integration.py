"""Integration tests for the walker module."""

from __future__ import annotations

from pathlib import Path

import pytest

from envoy.walker import collect_env_files, summarize_walk
from envoy.parser import parse_env_file


@pytest.fixture()
def rich_tree(tmp_path: Path) -> Path:
    """Multi-level directory tree with varied .env files."""
    envs = {
        ".env": "APP_ENV=production\nAPP_PORT=8080\n",
        "frontend/.env": "REACT_APP_API=http://localhost\n",
        "frontend/.env.local": "REACT_APP_DEBUG=true\n",
        "backend/.env": "DB_URL=postgres://localhost/db\nSECRET_KEY=abc123\n",
        "backend/tests/.env.example": "DB_URL=\nSECRET_KEY=\n",
    }
    for rel, content in envs.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    # non-env file that should be ignored
    (tmp_path / "docker-compose.yml").write_text("version: '3'\n")
    return tmp_path


def test_integration_all_env_files_discovered(rich_tree: Path):
    files = collect_env_files(rich_tree)
    assert len(files) == 5


def test_integration_no_non_env_files(rich_tree: Path):
    files = collect_env_files(rich_tree)
    for f in files:
        assert f.name not in {"docker-compose.yml"}


def test_integration_files_are_parseable(rich_tree: Path):
    files = collect_env_files(rich_tree)
    for f in files:
        env = parse_env_file(str(f))
        assert isinstance(env, dict)


def test_integration_summary_totals_match(rich_tree: Path):
    info = summarize_walk(rich_tree)
    assert info["total_files"] == 5
    assert info["total_dirs"] >= 3


def test_integration_depth_limit_reduces_results(rich_tree: Path):
    shallow = collect_env_files(rich_tree, max_depth=1)
    deep = collect_env_files(rich_tree, max_depth=10)
    assert len(shallow) < len(deep)
