"""digester.py — Compute and compare checksums for .env files and dicts."""

from __future__ import annotations

import hashlib
import json
from typing import Dict, Optional

ENV = Dict[str, str]

SUPPORTED_ALGORITHMS = ("md5", "sha1", "sha256", "sha512")


class DigestError(ValueError):
    """Raised when an unsupported algorithm is requested."""


def _canonical_bytes(env: ENV) -> bytes:
    """Produce a stable, canonical byte representation of an env dict."""
    ordered = json.dumps(dict(sorted(env.items())), separators=(",", ":"))
    return ordered.encode("utf-8")


def digest_env(env: ENV, algorithm: str = "sha256") -> str:
    """Return a hex digest of the env dict using *algorithm*.

    Keys are sorted before hashing so insertion order does not affect
    the result.
    """
    if algorithm not in SUPPORTED_ALGORITHMS:
        raise DigestError(
            f"Unsupported algorithm '{algorithm}'. "
            f"Choose from: {', '.join(SUPPORTED_ALGORITHMS)}"
        )
    h = hashlib.new(algorithm)
    h.update(_canonical_bytes(env))
    return h.hexdigest()


def digest_file(path: str, algorithm: str = "sha256") -> str:
    """Return a hex digest of a raw .env file's bytes."""
    if algorithm not in SUPPORTED_ALGORITHMS:
        raise DigestError(
            f"Unsupported algorithm '{algorithm}'. "
            f"Choose from: {', '.join(SUPPORTED_ALGORITHMS)}"
        )
    h = hashlib.new(algorithm)
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def envs_match(a: ENV, b: ENV, algorithm: str = "sha256") -> bool:
    """Return True when both env dicts produce the same digest."""
    return digest_env(a, algorithm) == digest_env(b, algorithm)


def changed_keys(a: ENV, b: ENV) -> Dict[str, tuple]:
    """Return a mapping of keys whose values differ between *a* and *b*.

    The value is a tuple (old_value, new_value).  Keys only present in
    one dict are included with None as the missing side.
    """
    all_keys = set(a) | set(b)
    return {
        k: (a.get(k), b.get(k))
        for k in sorted(all_keys)
        if a.get(k) != b.get(k)
    }
