"""Tests for envoy.caster and envoy.cli_cast."""

import argparse
import pytest
from unittest.mock import patch, MagicMock

from envoy.caster import (
    cast_to, cast_back, cast_env, get_cast_keys, list_types, CastError,
)
from envoy.cli_cast import build_parser, run_cast


# --- cast_to ---

def test_cast_to_str_returns_string():
    assert cast_to("hello", "str") == "hello"


def test_cast_to_int_valid():
    assert cast_to("42", "int") == 42


def test_cast_to_int_invalid_raises():
    with pytest.raises(CastError):
        cast_to("abc", "int")


def test_cast_to_float_valid():
    assert cast_to("3.14", "float") == pytest.approx(3.14)


def test_cast_to_float_invalid_raises():
    with pytest.raises(CastError):
        cast_to("not_a_float", "float")


def test_cast_to_bool_true_variants():
    for val in ("1", "true", "yes", "on", "True", "YES"):
        assert cast_to(val, "bool") is True


def test_cast_to_bool_false_variants():
    for val in ("0", "false", "no", "off", "", "False"):
        assert cast_to(val, "bool") is False


def test_cast_to_bool_invalid_raises():
    with pytest.raises(CastError):
        cast_to("maybe", "bool")


def test_cast_to_list_splits_by_delimiter():
    assert cast_to("a,b,c", "list") == ["a", "b", "c"]


def test_cast_to_list_custom_delimiter():
    assert cast_to("x|y|z", "list", delimiter="|") == ["x", "y", "z"]


def test_cast_to_list_empty_returns_empty_list():
    assert cast_to("", "list") == []


def test_cast_to_unknown_type_raises():
    with pytest.raises(CastError, match="Unknown type"):
        cast_to("val", "bytes")


# --- cast_back ---

def test_cast_back_bool_true():
    assert cast_back(True) == "true"


def test_cast_back_bool_false():
    assert cast_back(False) == "false"


def test_cast_back_list():
    assert cast_back(["a", "b"]) == "a,b"


def test_cast_back_int():
    assert cast_back(99) == "99"


# --- cast_env ---

def test_cast_env_casts_all_keys():
    env = {"PORT": "8080", "WORKERS": "4"}
    result = cast_env(env, "int")
    assert result == {"PORT": 8080, "WORKERS": 4}


def test_cast_env_casts_selected_keys():
    env = {"PORT": "8080", "NAME": "app"}
    result = cast_env(env, "int", keys=["PORT"])
    assert result["PORT"] == 8080
    assert result["NAME"] == "app"


def test_cast_env_missing_key_raises():
    with pytest.raises(CastError, match="Key not found"):
        cast_env({"A": "1"}, "int", keys=["MISSING"])


def test_cast_env_does_not_mutate_original():
    env = {"X": "10"}
    cast_env(env, "int")
    assert env["X"] == "10"


# --- get_cast_keys ---

def test_get_cast_keys_returns_castable_only():
    env = {"PORT": "8080", "NAME": "app", "TIMEOUT": "30"}
    result = get_cast_keys(env, "int")
    assert "PORT" in result
    assert "TIMEOUT" in result
    assert "NAME" not in result


# --- list_types ---

def test_list_types_contains_expected():
    types = list_types()
    for t in ("str", "int", "float", "bool", "list"):
        assert t in types


# --- CLI ---

@pytest.fixture
def tmp_env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("PORT=8080\nDEBUG=true\nFEATURES=a,b,c\n")
    return f


def make_args(tmp_env_file, typename, **kwargs):
    defaults = {
        "file": str(tmp_env_file),
        "type": typename,
        "keys": None,
        "delimiter": ",",
        "dry_run": False,
        "output": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_parser_returns_parser():
    p = build_parser()
    assert isinstance(p, argparse.ArgumentParser)


def test_cast_dry_run_prints_changed(tmp_env_file, capsys):
    args = make_args(tmp_env_file, "bool", keys=["DEBUG"], dry_run=True)
    rc = run_cast(args)
    assert rc == 0


def test_cast_writes_file(tmp_env_file):
    args = make_args(tmp_env_file, "str")
    rc = run_cast(args)
    assert rc == 0
    assert tmp_env_file.exists()


def test_cast_missing_file_returns_error(tmp_path):
    args = make_args(tmp_path / "missing.env", "int")
    rc = run_cast(args)
    assert rc == 1


def test_cast_invalid_value_returns_error(tmp_env_file):
    args = make_args(tmp_env_file, "int", keys=["FEATURES"])
    rc = run_cast(args)
    assert rc == 1
