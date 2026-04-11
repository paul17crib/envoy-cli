"""Tests for envoy.injector and envoy.cli_inject."""

from __future__ import annotations

import os
import sys
import argparse
from unittest.mock import patch, MagicMock

import pytest

from envoy.injector import (
    InjectionError,
    build_env,
    inject_into_os,
    keys_not_in_os,
    run_with_env,
)
from envoy.cli_inject import build_parser, run_inject


# ---------------------------------------------------------------------------
# injector unit tests
# ---------------------------------------------------------------------------

def test_inject_into_os_sets_keys():
    env = {"_ENVOY_TEST_KEY": "hello"}
    try:
        injected = inject_into_os(env)
        assert "_ENVOY_TEST_KEY" in injected
        assert os.environ["_ENVOY_TEST_KEY"] == "hello"
    finally:
        os.environ.pop("_ENVOY_TEST_KEY", None)


def test_inject_into_os_no_overwrite_skips_existing():
    os.environ["_ENVOY_EXISTING"] = "original"
    try:
        injected = inject_into_os({"_ENVOY_EXISTING": "new"}, overwrite=False)
        assert "_ENVOY_EXISTING" not in injected
        assert os.environ["_ENVOY_EXISTING"] == "original"
    finally:
        os.environ.pop("_ENVOY_EXISTING", None)


def test_build_env_inherits_os_environ():
    result = build_env({"MY_VAR": "1"}, inherit=True)
    assert "MY_VAR" in result
    # Should also contain existing env keys
    assert len(result) > 1


def test_build_env_no_inherit_only_provided():
    result = build_env({"ONLY_KEY": "val"}, inherit=False)
    assert result == {"ONLY_KEY": "val"}


def test_run_with_env_raises_on_empty_command():
    with pytest.raises(InjectionError):
        run_with_env([], {"KEY": "val"})


def test_run_with_env_passes_env_to_subprocess():
    result = run_with_env(
        [sys.executable, "-c", "import os, sys; sys.exit(0 if os.environ.get('_ENVOY_RUN')=='yes' else 1)"],
        {"_ENVOY_RUN": "yes"},
        capture_output=True,
    )
    assert result.returncode == 0


def test_keys_not_in_os_detects_missing():
    os.environ.pop("_ENVOY_MISSING_KEY", None)
    missing = keys_not_in_os({"_ENVOY_MISSING_KEY": "x", "PATH": "/bin"})
    assert "_ENVOY_MISSING_KEY" in missing
    assert "PATH" not in missing


# ---------------------------------------------------------------------------
# cli_inject tests
# ---------------------------------------------------------------------------

def test_build_parser_returns_parser():
    parser = build_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_run_inject_no_command_returns_error(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\n")
    args = argparse.Namespace(file=str(env_file), no_inherit=False, timeout=None, command=[])
    assert run_inject(args) == 1


def test_run_inject_missing_env_file_returns_error(tmp_path):
    args = argparse.Namespace(
        file=str(tmp_path / "missing.env"),
        no_inherit=False, timeout=None,
        command=[sys.executable, "-c", "pass"],
    )
    assert run_inject(args) == 1


def test_run_inject_runs_command(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("_ENVOY_CI=true\n")
    args = argparse.Namespace(
        file=str(env_file),
        no_inherit=False,
        timeout=10,
        command=[sys.executable, "-c",
                 "import os, sys; sys.exit(0 if os.environ.get('_ENVOY_CI')=='true' else 2)"],
    )
    assert run_inject(args) == 0


def test_run_inject_strips_double_dash_separator(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("X=1\n")
    args = argparse.Namespace(
        file=str(env_file),
        no_inherit=False,
        timeout=10,
        command=["--", sys.executable, "-c", "pass"],
    )
    assert run_inject(args) == 0
