"""Encode and decode .env values using common encoding schemes."""

from __future__ import annotations

import base64
import urllib.parse
from typing import Callable


class EncoderError(ValueError):
    """Raised when encoding or decoding fails."""


_ENCODERS: dict[str, Callable[[str], str]] = {
    "base64": lambda v: base64.b64encode(v.encode()).decode(),
    "base64url": lambda v: base64.urlsafe_b64encode(v.encode()).decode(),
    "urlencode": lambda v: urllib.parse.quote(v, safe=""),
    "hex": lambda v: v.encode().hex(),
}

_DECODERS: dict[str, Callable[[str], str]] = {
    "base64": lambda v: base64.b64decode(v).decode(),
    "base64url": lambda v: base64.urlsafe_b64decode(v).decode(),
    "urlencode": lambda v: urllib.parse.unquote(v),
    "hex": lambda v: bytes.fromhex(v).decode(),
}


def list_schemes() -> list[str]:
    """Return supported encoding scheme names."""
    return sorted(_ENCODERS.keys())


def encode_value(value: str, scheme: str) -> str:
    """Encode a single value using the given scheme."""
    fn = _ENCODERS.get(scheme)
    if fn is None:
        raise EncoderError(f"Unknown encoding scheme: {scheme!r}. Choose from: {list_schemes()}")
    try:
        return fn(value)
    except Exception as exc:
        raise EncoderError(f"Encoding failed with scheme {scheme!r}: {exc}") from exc


def decode_value(value: str, scheme: str) -> str:
    """Decode a single value using the given scheme."""
    fn = _DECODERS.get(scheme)
    if fn is None:
        raise EncoderError(f"Unknown encoding scheme: {scheme!r}. Choose from: {list_schemes()}")
    try:
        return fn(value)
    except Exception as exc:
        raise EncoderError(f"Decoding failed with scheme {scheme!r}: {exc}") from exc


def encode_env(
    env: dict[str, str],
    scheme: str,
    *,
    keys: list[str] | None = None,
) -> dict[str, str]:
    """Return a new env dict with specified (or all) values encoded."""
    result = dict(env)
    targets = keys if keys is not None else list(env.keys())
    for key in targets:
        if key in result:
            result[key] = encode_value(result[key], scheme)
    return result


def decode_env(
    env: dict[str, str],
    scheme: str,
    *,
    keys: list[str] | None = None,
) -> dict[str, str]:
    """Return a new env dict with specified (or all) values decoded."""
    result = dict(env)
    targets = keys if keys is not None else list(env.keys())
    for key in targets:
        if key in result:
            result[key] = decode_value(result[key], scheme)
    return result


def get_encoded_keys(original: dict[str, str], encoded: dict[str, str]) -> list[str]:
    """Return keys whose values differ between original and encoded dicts."""
    return [k for k in original if original.get(k) != encoded.get(k)]
