"""converter.py — Core conversion utilities for transforming env dicts."""

import json
from typing import Dict

from envoy.parser import serialize_env
from envoy.cli_export import format_bash, format_docker, format_yaml

FORMAT_EXTENSIONS = {
    "env": ".env",
    "bash": ".sh",
    "docker": ".txt",
    "yaml": ".yaml",
    "json": ".json",
}


def env_to_json(env: Dict[str, str], indent: int = 2) -> str:
    """Serialize env dict to JSON string."""
    return json.dumps(env, indent=indent)


def env_to_env(env: Dict[str, str]) -> str:
    """Serialize env dict back to .env format."""
    return serialize_env(env)


def env_to_bash(env: Dict[str, str]) -> str:
    """Serialize env dict to bash export statements."""
    return format_bash(env)


def env_to_docker(env: Dict[str, str]) -> str:
    """Serialize env dict to docker --env flags."""
    return format_docker(env)


def env_to_yaml(env: Dict[str, str]) -> str:
    """Serialize env dict to YAML key-value pairs."""
    return format_yaml(env)


FORMAT_HANDLERS = {
    "env": env_to_env,
    "bash": env_to_bash,
    "docker": env_to_docker,
    "yaml": env_to_yaml,
    "json": env_to_json,
}


def convert(env: Dict[str, str], to_format: str) -> str:
    """Convert env dict to the specified output format.

    Args:
        env: Dictionary of environment variables.
        to_format: Target format string (env, bash, docker, yaml, json).

    Returns:
        Formatted string in the requested format.

    Raises:
        ValueError: If the format is not supported.
    """
    handler = FORMAT_HANDLERS.get(to_format)
    if handler is None:
        supported = ", ".join(sorted(FORMAT_HANDLERS.keys()))
        raise ValueError(
            f"Unsupported format: '{to_format}'. Supported: {supported}"
        )
    return handler(env)


def suggested_filename(base: str, to_format: str) -> str:
    """Suggest an output filename based on format."""
    ext = FORMAT_EXTENSIONS.get(to_format, ".txt")
    stem = base.rstrip(".env").rstrip(".") or "output"
    return f"{stem}{ext}"
