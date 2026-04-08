"""Secret masking utilities for envoy-cli."""

import re
from typing import Dict, Set

# Keys that are considered sensitive and should be masked
DEFAULT_SENSITIVE_PATTERNS = [
    r".*SECRET.*",
    r".*PASSWORD.*",
    r".*PASSWD.*",
    r".*TOKEN.*",
    r".*API_KEY.*",
    r".*PRIVATE_KEY.*",
    r".*AUTH.*",
    r".*CREDENTIAL.*",
    r".*ACCESS_KEY.*",
]

MASK_VALUE = "********"


def is_sensitive_key(key: str, patterns: list[str] | None = None) -> bool:
    """Return True if the key matches any sensitive pattern."""
    patterns = patterns or DEFAULT_SENSITIVE_PATTERNS
    upper_key = key.upper()
    return any(re.fullmatch(pattern, upper_key) for pattern in patterns)


def mask_env(env: Dict[str, str], patterns: list[str] | None = None) -> Dict[str, str]:
    """Return a copy of env dict with sensitive values masked."""
    return {
        key: (MASK_VALUE if is_sensitive_key(key, patterns) else value)
        for key, value in env.items()
    }


def get_masked_keys(env: Dict[str, str], patterns: list[str] | None = None) -> Set[str]:
    """Return the set of keys whose values would be masked."""
    return {key for key in env if is_sensitive_key(key, patterns)}
