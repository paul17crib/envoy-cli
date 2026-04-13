"""Sample a subset of keys from an env dictionary."""

from __future__ import annotations

import random
from typing import Dict, List, Optional


class SamplerError(Exception):
    """Raised when sampling cannot be completed."""


def sample_keys(
    env: Dict[str, str],
    n: int,
    *,
    seed: Optional[int] = None,
    keys: Optional[List[str]] = None,
) -> Dict[str, str]:
    """Return a random sample of *n* key/value pairs from *env*.

    Args:
        env: Source environment dictionary.
        n: Number of keys to sample.
        seed: Optional random seed for reproducibility.
        keys: If provided, sample only from these keys.

    Returns:
        A new dict containing the sampled pairs.

    Raises:
        SamplerError: If *n* exceeds the available pool or *n* < 0.
    """
    pool = list(keys) if keys is not None else list(env.keys())
    # Validate requested keys exist
    missing = [k for k in pool if k not in env]
    if missing:
        raise SamplerError(f"Keys not found in env: {', '.join(missing)}")
    if n < 0:
        raise SamplerError(f"Sample size must be non-negative, got {n}.")
    if n > len(pool):
        raise SamplerError(
            f"Requested sample size {n} exceeds available pool of {len(pool)}."
        )
    rng = random.Random(seed)
    chosen = rng.sample(pool, n)
    return {k: env[k] for k in chosen}


def sample_fraction(
    env: Dict[str, str],
    fraction: float,
    *,
    seed: Optional[int] = None,
) -> Dict[str, str]:
    """Return a fractional sample of *env*.

    Args:
        env: Source environment dictionary.
        fraction: Value between 0.0 and 1.0 (inclusive).
        seed: Optional random seed.

    Returns:
        Sampled dict.

    Raises:
        SamplerError: If *fraction* is outside [0, 1].
    """
    if not (0.0 <= fraction <= 1.0):
        raise SamplerError(f"Fraction must be between 0.0 and 1.0, got {fraction}.")
    n = round(len(env) * fraction)
    return sample_keys(env, n, seed=seed)


def get_sampled_keys(result: Dict[str, str]) -> List[str]:
    """Return sorted list of keys from a sampled env dict."""
    return sorted(result.keys())
