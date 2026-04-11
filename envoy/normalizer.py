"""Normalize .env variable values: strip whitespace, fix quoting, standardize booleans."""

from typing import Dict, Optional

TRUE_VALUES = {"true", "yes", "1", "on"}
FALSE_VALUES = {"false", "no", "0", "off"}


def normalize_boolean(value: str) -> Optional[str]:
    """Return 'true' or 'false' if value looks like a boolean, else None."""
    lower = value.strip().lower()
    if lower in TRUE_VALUES:
        return "true"
    if lower in FALSE_VALUES:
        return "false"
    return None


def normalize_value(value: str, fix_booleans: bool = True, strip_whitespace: bool = True) -> str:
    """Normalize a single env value.

    Args:
        value: Raw env value string.
        fix_booleans: Standardize boolean-like values to 'true'/'false'.
        strip_whitespace: Strip leading/trailing whitespace from value.

    Returns:
        Normalized value string.
    """
    if strip_whitespace:
        value = value.strip()

    if fix_booleans:
        bool_result = normalize_boolean(value)
        if bool_result is not None:
            return bool_result

    return value


def normalize_env(
    env: Dict[str, str],
    fix_booleans: bool = True,
    strip_whitespace: bool = True,
    uppercase_keys: bool = False,
) -> Dict[str, str]:
    """Normalize all values (and optionally keys) in an env dict.

    Args:
        env: Original env mapping.
        fix_booleans: Standardize boolean-like values.
        strip_whitespace: Strip whitespace from values.
        uppercase_keys: Convert all keys to uppercase.

    Returns:
        New normalized env dict (does not mutate original).
    """
    result: Dict[str, str] = {}
    for key, value in env.items():
        normalized_key = key.upper() if uppercase_keys else key
        normalized_value = normalize_value(
            value, fix_booleans=fix_booleans, strip_whitespace=strip_whitespace
        )
        result[normalized_key] = normalized_value
    return result


def get_normalized_keys(original: Dict[str, str], normalized: Dict[str, str]) -> Dict[str, str]:
    """Return only the keys whose values changed during normalization."""
    return {
        key: normalized[key]
        for key in original
        if key in normalized and original[key] != normalized[key]
    }
