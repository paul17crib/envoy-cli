"""Tests for envoy.typer."""

import pytest

from envoy.typer import (
    TyperError,
    cast_value,
    get_typed_keys,
    infer_type,
    type_env,
)


# ---------------------------------------------------------------------------
# infer_type
# ---------------------------------------------------------------------------

def test_infer_type_bool_true_variants():
    for v in ("true", "True", "TRUE", "yes", "1", "on"):
        assert infer_type(v) == "bool", v


def test_infer_type_bool_false_variants():
    for v in ("false", "False", "no", "0", "off"):
        assert infer_type(v) == "bool", v


def test_infer_type_int():
    assert infer_type("42") == "int"
    assert infer_type("-7") == "int"


def test_infer_type_float():
    assert infer_type("3.14") == "float"
    assert infer_type("-0.5") == "float"


def test_infer_type_str():
    assert infer_type("hello") == "str"
    assert infer_type("") == "str"
    assert infer_type("localhost:5432") == "str"


# ---------------------------------------------------------------------------
# cast_value
# ---------------------------------------------------------------------------

def test_cast_value_str():
    assert cast_value("hello", "str") == "hello"


def test_cast_value_int_valid():
    assert cast_value("10", "int") == 10


def test_cast_value_int_invalid_raises():
    with pytest.raises(TyperError):
        cast_value("abc", "int")


def test_cast_value_float_valid():
    assert cast_value("2.5", "float") == pytest.approx(2.5)


def test_cast_value_float_invalid_raises():
    with pytest.raises(TyperError):
        cast_value("xyz", "float")


def test_cast_value_bool_true():
    assert cast_value("true", "bool") is True
    assert cast_value("YES", "bool") is True


def test_cast_value_bool_false():
    assert cast_value("false", "bool") is False
    assert cast_value("0", "bool") is False


def test_cast_value_bool_invalid_raises():
    with pytest.raises(TyperError):
        cast_value("maybe", "bool")


def test_cast_value_unknown_type_raises():
    with pytest.raises(TyperError):
        cast_value("x", "list")


# ---------------------------------------------------------------------------
# type_env
# ---------------------------------------------------------------------------

def test_type_env_returns_correct_types():
    env = {"PORT": "8080", "DEBUG": "true", "HOST": "localhost", "RATIO": "0.5"}
    result = type_env(env)
    assert result["PORT"] == ("int", 8080)
    assert result["DEBUG"] == ("bool", True)
    assert result["HOST"] == ("str", "localhost")
    assert result["RATIO"][0] == "float"


def test_type_env_empty():
    assert type_env({}) == {}


# ---------------------------------------------------------------------------
# get_typed_keys
# ---------------------------------------------------------------------------

def test_get_typed_keys_filters_by_type():
    env = {"A": "1", "B": "hello", "C": "true", "D": "99"}
    ints = get_typed_keys(env, "int")
    assert set(ints.keys()) == {"A", "D"}
    assert ints["A"] == 1


def test_get_typed_keys_no_match_returns_empty():
    env = {"X": "hello", "Y": "world"}
    assert get_typed_keys(env, "bool") == {}
