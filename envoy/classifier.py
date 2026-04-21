"""Classify env keys and values into semantic categories."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envoy.masker import is_sensitive_key

CATEGORY_PATTERNS: Dict[str, List[str]] = {
    "database": ["db", "database", "postgres", "mysql", "mongo", "redis", "sqlite"],
    "auth": ["secret", "token", "password", "passwd", "auth", "jwt", "oauth", "api_key"],
    "network": ["host", "port", "url", "uri", "endpoint", "addr", "address"],
    "storage": ["bucket", "s3", "storage", "disk", "path", "dir", "directory"],
    "feature": ["feature", "flag", "enable", "disable", "toggle"],
    "logging": ["log", "logger", "logging", "level", "debug", "verbose"],
    "environment": ["env", "environment", "stage", "region", "zone"],
}


@dataclass
class ClassifiedKey:
    key: str
    value: str
    category: str
    sensitive: bool
    tags: List[str] = field(default_factory=list)


def classify_key(key: str) -> str:
    """Return the best-matching category for a key name."""
    lower = key.lower()
    for category, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if pattern in lower:
                return category
    return "general"


def classify_env(
    env: Dict[str, str],
    extra_patterns: Dict[str, List[str]] | None = None,
) -> Dict[str, ClassifiedKey]:
    """Classify every key in an env dict.

    Returns a mapping of key -> ClassifiedKey.
    """
    patterns = dict(CATEGORY_PATTERNS)
    if extra_patterns:
        for cat, pats in extra_patterns.items():
            patterns.setdefault(cat, []).extend(pats)

    result: Dict[str, ClassifiedKey] = {}
    for key, value in env.items():
        lower = key.lower()
        category = "general"
        for cat, pats in patterns.items():
            if any(p in lower for p in pats):
                category = cat
                break
        result[key] = ClassifiedKey(
            key=key,
            value=value,
            category=category,
            sensitive=is_sensitive_key(key),
        )
    return result


def group_by_category(
    classified: Dict[str, ClassifiedKey],
) -> Dict[str, List[ClassifiedKey]]:
    """Group ClassifiedKey objects by their category."""
    groups: Dict[str, List[ClassifiedKey]] = {}
    for ck in classified.values():
        groups.setdefault(ck.category, []).append(ck)
    return groups


def list_categories() -> List[str]:
    """Return the built-in category names."""
    return list(CATEGORY_PATTERNS.keys()) + ["general"]
