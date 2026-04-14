"""Obfuscator: partially reveal or scramble env values for safe sharing."""

import re
from typing import Dict, Optional


class ObfuscatorError(Exception):
    pass


def _validate_reveal(reveal: int) -> None:
    if reveal < 0:
        raise ObfuscatorError("reveal must be >= 0")


def partial_reveal(value: str, reveal: int = 4, mask_char: str = "*") -> str:
    """Show only the first `reveal` characters; mask the rest."""
    _validate_reveal(reveal)
    if not value:
        return value
    visible = value[:reveal]
    hidden = mask_char * max(len(value) - reveal, 0)
    return visible + hidden


def scramble_value(value: str, mask_char: str = "*") -> str:
    """Replace every character with the mask character, preserving length."""
    return mask_char * len(value)


def obfuscate_env(
    env: Dict[str, str],
    keys: Optional[list] = None,
    reveal: int = 4,
    mask_char: str = "*",
    scramble: bool = False,
) -> Dict[str, str]:
    """Return a copy of env with selected keys obfuscated.

    If `keys` is None, all keys are obfuscated.
    If `scramble` is True, values are fully masked regardless of `reveal`.
    """
    _validate_reveal(reveal)
    result = dict(env)
    targets = keys if keys is not None else list(env.keys())
    for key in targets:
        if key not in result:
            continue
        val = result[key]
        if scramble:
            result[key] = scramble_value(val, mask_char)
        else:
            result[key] = partial_reveal(val, reveal, mask_char)
    return result


def get_obfuscated_keys(
    original: Dict[str, str], obfuscated: Dict[str, str]
) -> list:
    """Return list of keys whose values differ between original and obfuscated."""
    return [
        k for k in original
        if k in obfuscated and original[k] != obfuscated[k]
    ]
