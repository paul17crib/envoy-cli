"""Type inference and casting for .env values."""

from __future__ import annotations

from typing import Any


class TyperError(Exception):
    """Raised when a type cast fails."""


_BOOL_TRUE = {"true", "yes", "1", "on"}
_BOOL_FALSE = {"false", "no", "0", "off"}


def infer_type(value: str) -> str:
    """Return the inferred type name for a string value."""
    if value.lower() in _BOOL_TRUE | _BOOL_FALSE:
        return "bool"
    try:
        int(value)
        return "int"
    except ValueError:
        pass
    try:
        float(value)
        return "float"
    except ValueError:
        pass
    return "str"


def cast_value(value: str, as_type: str) -> Any:
    """Cast a string value to the given type name.

    Supported types: str, int, float, bool.
    Raises TyperError on failure.
    """
    as_type = as_type.lower()
    if as_type == "str":
        return value
    if as_type == "int":
        try:
            return int(value)
        except ValueError:
            raise TyperError(f"Cannot cast {value!r} to int")
    if as_type == "float":
        try:
            return float(value)
        except ValueError:
            raise TyperError(f"Cannot cast {value!r} to float")
    if as_type == "bool":
        if value.lower() in _BOOL_TRUE:
            return True
        if value.lower() in _BOOL_FALSE:
            return False
        raise TyperError(f"Cannot cast {value!r} to bool")
    raise TyperError(f"Unknown type: {as_type!r}")


def type_env(env: dict[str, str]) -> dict[str, tuple[str, Any]]:
    """Return a mapping of key -> (inferred_type, cast_value) for every entry."""
    result: dict[str, tuple[str, Any]] = {}
    for key, value in env.items():
        t = infer_type(value)
        result[key] = (t, cast_value(value, t))
    return result


def get_typed_keys(
    env: dict[str, str], target_type: str
) -> dict[str, Any]:
    """Return keys whose inferred type matches *target_type*."""
    target_type = target_type.lower()
    return {
        k: cast_value(v, target_type)
        for k, v in env.items()
        if infer_type(v) == target_type
    }
