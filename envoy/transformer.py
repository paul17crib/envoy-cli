"""Transform env values using built-in or custom transformation functions."""

from typing import Callable, Dict, List, Optional

TransformFn = Callable[[str], str]

BUILTIN_TRANSFORMS: Dict[str, TransformFn] = {
    "upper": str.upper,
    "lower": str.lower,
    "strip": str.strip,
    "title": str.title,
    "reverse": lambda v: v[::-1],
    "base64": lambda v: __import__("base64").b64encode(v.encode()).decode(),
    "unbase64": lambda v: __import__("base64").b64decode(v.encode()).decode(),
    "urlencode": lambda v: __import__("urllib.parse", fromlist=["quote"]).quote(v, safe=""),
}


class TransformError(Exception):
    """Raised when a transformation fails."""


def get_transform(name: str) -> TransformFn:
    """Return a built-in transform function by name."""
    if name not in BUILTIN_TRANSFORMS:
        available = ", ".join(sorted(BUILTIN_TRANSFORMS))
        raise TransformError(f"Unknown transform '{name}'. Available: {available}")
    return BUILTIN_TRANSFORMS[name]


def transform_value(value: str, transforms: List[str]) -> str:
    """Apply a sequence of named transforms to a value."""
    result = value
    for name in transforms:
        fn = get_transform(name)
        try:
            result = fn(result)
        except Exception as exc:
            raise TransformError(f"Transform '{name}' failed: {exc}") from exc
    return result


def transform_env(
    env: Dict[str, str],
    transforms: List[str],
    keys: Optional[List[str]] = None,
) -> Dict[str, str]:
    """Apply transforms to all (or selected) keys in an env dict.

    Returns a new dict; does not mutate the original.
    """
    result = dict(env)
    target_keys = keys if keys is not None else list(env.keys())
    for key in target_keys:
        if key in result:
            result[key] = transform_value(result[key], transforms)
    return result


def get_transformed_keys(
    original: Dict[str, str],
    transformed: Dict[str, str],
) -> List[str]:
    """Return list of keys whose values changed after transformation."""
    return [k for k in original if original.get(k) != transformed.get(k)]
