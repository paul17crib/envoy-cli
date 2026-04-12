"""Cast env values to typed Python objects or back to strings."""

from typing import Any, Dict, Optional


class CastError(Exception):
    pass


_CAST_TYPES = ("str", "int", "float", "bool", "list")


def list_types() -> list:
    """Return supported cast type names."""
    return list(_CAST_TYPES)


def cast_to(value: str, typename: str, delimiter: str = ",") -> Any:
    """Cast a string value to the given type name."""
    if typename == "str":
        return value
    if typename == "int":
        try:
            return int(value)
        except ValueError:
            raise CastError(f"Cannot cast {value!r} to int")
    if typename == "float":
        try:
            return float(value)
        except ValueError:
            raise CastError(f"Cannot cast {value!r} to float")
    if typename == "bool":
        if value.lower() in ("1", "true", "yes", "on"):
            return True
        if value.lower() in ("0", "false", "no", "off", ""):
            return False
        raise CastError(f"Cannot cast {value!r} to bool")
    if typename == "list":
        if not value:
            return []
        return [item.strip() for item in value.split(delimiter)]
    raise CastError(f"Unknown type: {typename!r}. Choose from {_CAST_TYPES}")


def cast_back(value: Any) -> str:
    """Convert a typed Python value back to a string suitable for .env files."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return ",".join(str(v) for v in value)
    return str(value)


def cast_env(
    env: Dict[str, str],
    typename: str,
    keys: Optional[list] = None,
    delimiter: str = ",",
) -> Dict[str, Any]:
    """Cast selected (or all) keys in env to typename. Returns new dict."""
    result = dict(env)
    targets = keys if keys is not None else list(env.keys())
    for key in targets:
        if key not in env:
            raise CastError(f"Key not found: {key!r}")
        result[key] = cast_to(env[key], typename, delimiter=delimiter)
    return result


def get_cast_keys(
    env: Dict[str, str],
    typename: str,
    delimiter: str = ",",
) -> Dict[str, Any]:
    """Return a mapping of key -> cast value for all keys that cast without error."""
    out = {}
    for key, val in env.items():
        try:
            out[key] = cast_to(val, typename, delimiter=delimiter)
        except CastError:
            pass
    return out
