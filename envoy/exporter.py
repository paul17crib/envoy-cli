"""Export env variables to various shell-friendly formats with optional masking."""

from __future__ import annotations

from typing import Dict

from envoy.masker import mask_env


class ExportError(Exception):
    pass


def export_as_shell(env: Dict[str, str], *, mask: bool = False) -> str:
    """Return env as shell export statements (export KEY=VALUE)."""
    data = mask_env(env) if mask else env
    lines = []
    for key, value in data.items():
        escaped = value.replace('"', '\\"')
        lines.append(f'export {key}="{escaped}"')
    return "\n".join(lines)


def export_as_inline(env: Dict[str, str], *, mask: bool = False) -> str:
    """Return env as a single-line KEY=VALUE string suitable for inline use."""
    data = mask_env(env) if mask else env
    pairs = []
    for key, value in data.items():
        escaped = value.replace('"', '\\"')
        pairs.append(f'{key}="{escaped}"')
    return " ".join(pairs)


def export_as_dotenv(env: Dict[str, str], *, mask: bool = False) -> str:
    """Return env as a plain .env file string."""
    data = mask_env(env) if mask else env
    lines = []
    for key, value in data.items():
        if any(c in value for c in (" ", "\t", "#", '"', "'")):
            escaped = value.replace('"', '\\"')
            lines.append(f'{key}="{escaped}"')
        else:
            lines.append(f"{key}={value}")
    return "\n".join(lines)


SCHEMES = {
    "shell": export_as_shell,
    "inline": export_as_inline,
    "dotenv": export_as_dotenv,
}


def list_schemes() -> list[str]:
    return sorted(SCHEMES.keys())


def export_env(env: Dict[str, str], scheme: str, *, mask: bool = False) -> str:
    """Export env using the named scheme."""
    if scheme not in SCHEMES:
        raise ExportError(
            f"Unknown export scheme '{scheme}'. Choose from: {', '.join(list_schemes())}"
        )
    return SCHEMES[scheme](env, mask=mask)
