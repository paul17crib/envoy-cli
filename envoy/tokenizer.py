"""Tokenizer: split env values into tokens for analysis or transformation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class TokenizerError(Exception):
    """Raised when tokenization fails."""


@dataclass
class TokenResult:
    key: str
    original: str
    tokens: List[str] = field(default_factory=list)

    def count(self) -> int:
        return len(self.tokens)

    def joined(self, sep: str = " ") -> str:
        return sep.join(self.tokens)


def tokenize_value(
    value: str,
    delimiter: Optional[str] = None,
    pattern: Optional[str] = None,
) -> List[str]:
    """Split a single value into tokens.

    If *pattern* is given it is used as a regex split pattern.
    If *delimiter* is given the value is split on that literal string.
    Otherwise the value is split on whitespace.
    """
    if pattern is not None:
        try:
            parts = re.split(pattern, value)
        except re.error as exc:
            raise TokenizerError(f"Invalid pattern {pattern!r}: {exc}") from exc
    elif delimiter is not None:
        parts = value.split(delimiter)
    else:
        parts = value.split()

    return [p for p in parts if p]


def tokenize_env(
    env: Dict[str, str],
    keys: Optional[List[str]] = None,
    delimiter: Optional[str] = None,
    pattern: Optional[str] = None,
) -> Dict[str, TokenResult]:
    """Tokenize values in *env*, returning a mapping of key -> TokenResult.

    Only keys in *keys* are processed; all keys are processed when *keys* is None.
    """
    target_keys = keys if keys is not None else list(env.keys())
    results: Dict[str, TokenResult] = {}
    for key in target_keys:
        if key not in env:
            raise TokenizerError(f"Key {key!r} not found in env")
        value = env[key]
        tokens = tokenize_value(value, delimiter=delimiter, pattern=pattern)
        results[key] = TokenResult(key=key, original=value, tokens=tokens)
    return results


def get_token_counts(results: Dict[str, TokenResult]) -> Dict[str, int]:
    """Return a mapping of key -> token count from tokenize_env results."""
    return {key: result.count() for key, result in results.items()}
