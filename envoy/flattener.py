"""Flatten nested prefix groups into a single env dict, or expand a flat env
into a nested structure represented as dot-separated keys."""

from typing import Dict, Optional


def flatten_nested(
    nested: Dict[str, Dict[str, str]],
    delimiter: str = "__",
) -> Dict[str, str]:
    """Convert a nested {group: {key: value}} mapping into a flat env dict.

    Example::

        {"DB": {"HOST": "localhost", "PORT": "5432"}}
        -> {"DB__HOST": "localhost", "DB__PORT": "5432"}
    """
    result: Dict[str, str] = {}
    for group, entries in nested.items():
        for key, value in entries.items():
            flat_key = f"{group}{delimiter}{key}" if group else key
            result[flat_key] = value
    return result


def expand_flat(
    env: Dict[str, str],
    delimiter: str = "__",
) -> Dict[str, Dict[str, str]]:
    """Convert a flat env dict into a nested {group: {key: value}} mapping.

    Keys without the delimiter are placed under an empty-string group.

    Example::

        {"DB__HOST": "localhost", "APP_NAME": "envoy"}
        -> {"DB": {"HOST": "localhost"}, "": {"APP_NAME": "envoy"}}
    """
    result: Dict[str, Dict[str, str]] = {}
    for key, value in env.items():
        if delimiter in key:
            group, _, remainder = key.partition(delimiter)
        else:
            group, remainder = "", key
        result.setdefault(group, {})[remainder] = value
    return result


def flatten_env(
    env: Dict[str, str],
    delimiter: str = "__",
    prefix: Optional[str] = None,
) -> Dict[str, str]:
    """Return only the entries that belong to *prefix* with the prefix stripped.

    If *prefix* is None, all keys are returned unchanged.

    Example::

        env = {"DB__HOST": "localhost", "DB__PORT": "5432", "APP_NAME": "x"}
        flatten_env(env, prefix="DB") -> {"HOST": "localhost", "PORT": "5432"}
    """
    if prefix is None:
        return dict(env)

    strip = f"{prefix}{delimiter}"
    return {
        key[len(strip):]: value
        for key, value in env.items()
        if key.startswith(strip)
    }


def list_prefixes(env: Dict[str, str], delimiter: str = "__") -> list:
    """Return a sorted list of unique prefixes found in the env keys."""
    prefixes = set()
    for key in env:
        if delimiter in key:
            prefixes.add(key.split(delimiter, 1)[0])
    return sorted(prefixes)
