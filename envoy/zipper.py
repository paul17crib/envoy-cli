"""Zip/unzip two env dicts by combining or splitting paired values."""
from __future__ import annotations

from typing import Dict, List, Tuple


class ZipperError(Exception):
    pass


def zip_envs(
    left: Dict[str, str],
    right: Dict[str, str],
    delimiter: str = "|",
    keys: List[str] | None = None,
) -> Dict[str, str]:
    """Combine values from two envs into a single env using a delimiter.

    Only keys present in *both* envs are zipped (or the subset given by `keys`).
    Keys exclusive to one side are passed through from the left env unchanged.
    """
    if not delimiter:
        raise ZipperError("delimiter must be a non-empty string")

    target_keys = set(keys) if keys is not None else set(left) | set(right)
    result: Dict[str, str] = dict(left)

    for key in target_keys:
        if key in left and key in right:
            result[key] = f"{left[key]}{delimiter}{right[key]}"
        elif key in right:
            result[key] = right[key]

    return result


def unzip_env(
    env: Dict[str, str],
    delimiter: str = "|",
    keys: List[str] | None = None,
) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Split zipped values back into two separate envs.

    Values that do not contain the delimiter are placed in the left env only.
    """
    if not delimiter:
        raise ZipperError("delimiter must be a non-empty string")

    target_keys = set(keys) if keys is not None else set(env)
    left: Dict[str, str] = {}
    right: Dict[str, str] = {}

    for key, value in env.items():
        if key in target_keys and delimiter in value:
            idx = value.index(delimiter)
            left[key] = value[:idx]
            right[key] = value[idx + len(delimiter):]
        else:
            left[key] = value

    return left, right


def get_zipped_keys(env: Dict[str, str], delimiter: str = "|") -> List[str]:
    """Return keys whose values contain the delimiter (i.e. were zipped)."""
    return [k for k, v in env.items() if delimiter in v]
