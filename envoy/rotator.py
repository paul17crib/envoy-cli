import secrets
import string
from dataclasses import dataclass, field
from typing import Dict, List


_ALPHABET = string.ascii_letters + string.digits


def generate_secret(length: int = 32) -> str:
    """Generate a cryptographically secure random secret string."""
    return "".join(secrets.choice(_ALPHABET) for _ in range(length))


@dataclass
class RotationPlan:
    """Holds the original env, the new env, and which keys were rotated."""
    original_env: Dict[str, str]
    new_env: Dict[str, str]
    rotated_keys: List[str] = field(default_factory=list)


def rotate_env(
    env: Dict[str, str],
    keys: List[str],
    length: int = 32,
) -> RotationPlan:
    """
    Produce a RotationPlan that replaces the values of *keys* with freshly
    generated secrets.  Keys that do not exist in *env* are skipped.
    """
    new_env = dict(env)
    rotated: List[str] = []

    for key in keys:
        if key in new_env:
            new_env[key] = generate_secret(length)
            rotated.append(key)

    return RotationPlan(
        original_env=env,
        new_env=new_env,
        rotated_keys=rotated,
    )
