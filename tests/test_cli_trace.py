"""Tests for envoy.cli_trace."""

from __future__ import annotations

from pathlib import Path

import pytest

from envoy.cli_trace import build_parser, run_trace


@pytest.fixture()
def env_and_src(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DATABASE_URL=postgres://localhost/db\n"
        "SECRET_KEY=supersecret\n"
        "UNUSED_VAR=nothing\n"
    )
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").write_text(
        'import os\n'
        'db = os.environ.get("DATABASE_URL")\n'
        'key = os.environ["SECRET_KEY"]\n'
    )
    return tmp_path, env_file, src


def make_args(directory: str, env_file: str = ".env", unused=False, undeclared=False, ext=None):
    parser = build_parser()
    argv = [directory, "--env-file", env_file]
    if unused:
        argv.append("--unused")
    if undeclared:
        argv.append("--undeclared")
    if ext:
        argv += ["--ext"] + ext
    return parser.parse_args(argv)


def test_build_parser_returns_parser() -> None:
    parser = build_parser()
    assert parser is not None


def test_run_trace_full_report(env_and_src, capsys) -> None:
    tmp, env_file, src = env_and_src
    args = make_args(str(src), env_file=str(env_file))
    rc = run_trace(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "DATABASE_URL" in out
    assert "SECRET_KEY" in out


def test_run_trace_unused_flag(env_and_src, capsys) -> None:
    tmp, env_file, src = env_and_src
    args = make_args(str(src), env_file=str(env_file), unused=True)
    rc = run_trace(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "UNUSED_VAR" in out
    assert "DATABASE_URL" not in out


def test_run_trace_unused_all_referenced(env_and_src, capsys) -> None:
    tmp, env_file, src = env_and_src
    # write env with only referenced keys
    env_file2 = tmp / ".env2"
    env_file2.write_text("DATABASE_URL=x\nSECRET_KEY=y\n")
    args = make_args(str(src), env_file=str(env_file2), unused=True)
    rc = run_trace(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "All keys are referenced" in out


def test_run_trace_undeclared_flag(env_and_src, capsys) -> None:
    tmp, env_file, src = env_and_src
    # env missing SECRET_KEY so it appears undeclared
    env_file2 = tmp / ".env3"
    env_file2.write_text("DATABASE_URL=x\n")
    args = make_args(str(src), env_file=str(env_file2), undeclared=True)
    rc = run_trace(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "SECRET_KEY" in out


def test_run_trace_missing_env_file(tmp_path, capsys) -> None:
    args = make_args(str(tmp_path), env_file=str(tmp_path / "missing.env"))
    rc = run_trace(args)
    assert rc == 1
    assert "error" in capsys.readouterr().out


def test_run_trace_missing_directory(env_and_src, capsys) -> None:
    tmp, env_file, src = env_and_src
    args = make_args(str(tmp / "no_such_dir"), env_file=str(env_file))
    rc = run_trace(args)
    assert rc == 1
    assert "error" in capsys.readouterr().out


def test_run_trace_ext_filter(env_and_src, capsys) -> None:
    tmp, env_file, src = env_and_src
    # Only scan .js files — nothing should match
    args = make_args(str(src), env_file=str(env_file), ext=[".js"])
    rc = run_trace(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "(not found)" in out
