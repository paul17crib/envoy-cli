"""Tests for envoy.composer and envoy.cli_compose."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envoy.composer import (
    ComposerError,
    compose,
    compose_with_fns,
    get_step,
    list_steps,
    preview_compose,
    register,
)
from envoy.cli_compose import build_parser, run_compose


# ---------------------------------------------------------------------------
# composer unit tests
# ---------------------------------------------------------------------------

def test_list_steps_returns_builtins():
    steps = list_steps()
    assert "strip_empty" in steps
    assert "upper_keys" in steps
    assert "lower_values" in steps
    assert "strip_whitespace" in steps


def test_get_step_returns_callable():
    fn = get_step("strip_empty")
    assert callable(fn)


def test_get_step_unknown_raises():
    with pytest.raises(ComposerError, match="Unknown"):
        get_step("nonexistent_step")


def test_compose_strip_empty_removes_blank_values():
    env = {"A": "hello", "B": "", "C": "world"}
    result = compose(env, ["strip_empty"])
    assert "B" not in result
    assert result["A"] == "hello"
    assert result["C"] == "world"


def test_compose_does_not_mutate_original():
    env = {"A": "hello", "B": ""}
    compose(env, ["strip_empty"])
    assert "B" in env


def test_compose_upper_keys():
    env = {"app_name": "myapp", "db_host": "localhost"}
    result = compose(env, ["upper_keys"])
    assert "APP_NAME" in result
    assert "DB_HOST" in result


def test_compose_strip_whitespace():
    env = {"KEY": "  padded  "}
    result = compose(env, ["strip_whitespace"])
    assert result["KEY"] == "padded"


def test_compose_chained_steps():
    env = {"key": "  HELLO  ", "empty": ""}
    result = compose(env, ["strip_whitespace", "strip_empty", "upper_keys"])
    assert result["KEY"] == "  HELLO  ".strip()
    assert "EMPTY" not in result


def test_compose_with_fns_applies_callables():
    env = {"A": "1", "B": "2"}
    result = compose_with_fns(env, [lambda e: {k: v + "!", **{}} for k, v in [("A", "1")]][:0] or [lambda e: {k: v + "!" for k, v in e.items()}])
    assert result["A"] == "1!"


def test_preview_compose_returns_snapshots():
    env = {"X": "hello", "Y": ""}
    snaps = preview_compose(env, ["strip_empty", "upper_keys"])
    assert len(snaps) == 2
    assert snaps[0]["step"] == "strip_empty"
    assert snaps[1]["step"] == "upper_keys"


def test_register_custom_step():
    register("reverse_values", lambda e: {k: v[::-1] for k, v in e.items()})
    result = compose({"MSG": "hello"}, ["reverse_values"])
    assert result["MSG"] == "olleh"


# ---------------------------------------------------------------------------
# cli_compose tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_env_file(tmp_path: Path) -> Path:
    f = tmp_path / ".env"
    f.write_text("APP_NAME=myapp\nDB_HOST=  localhost  \nEMPTY=\n")
    return f


def make_args(file: str, steps, **kwargs) -> argparse.Namespace:
    defaults = {"dry_run": False, "preview": False, "output": None}
    defaults.update(kwargs)
    return argparse.Namespace(file=file, steps=steps, **defaults)


def test_build_parser_returns_parser():
    p = build_parser()
    assert isinstance(p, argparse.ArgumentParser)


def test_compose_dry_run_does_not_modify_file(tmp_env_file: Path):
    original = tmp_env_file.read_text()
    args = make_args(str(tmp_env_file), ["strip_empty"], dry_run=True)
    rc = run_compose(args)
    assert rc == 0
    assert tmp_env_file.read_text() == original


def test_compose_writes_result_to_file(tmp_env_file: Path):
    args = make_args(str(tmp_env_file), ["strip_whitespace"])
    rc = run_compose(args)
    assert rc == 0
    content = tmp_env_file.read_text()
    assert "localhost" in content
    assert "  localhost  " not in content


def test_compose_missing_file_returns_error(tmp_path: Path):
    args = make_args(str(tmp_path / "missing.env"), ["strip_empty"])
    rc = run_compose(args)
    assert rc == 1


def test_compose_unknown_step_returns_error(tmp_env_file: Path):
    args = make_args(str(tmp_env_file), ["no_such_step"])
    rc = run_compose(args)
    assert rc == 1


def test_compose_output_to_different_file(tmp_env_file: Path, tmp_path: Path):
    out = tmp_path / "out.env"
    args = make_args(str(tmp_env_file), ["strip_empty"], output=str(out))
    rc = run_compose(args)
    assert rc == 0
    assert out.exists()
    assert "EMPTY" not in out.read_text()
