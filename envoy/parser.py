"""Parser for .env files with support for comments, quoted values, and multiline strings."""

import re
from typing import Dict, Optional

ENV_LINE_RE = re.compile(
    r"^\s*(?:export\s+)?"
    r"(?P<key>[A-Za-z_][A-Za-z0-9_]*)"
    r"\s*=\s*"
    r"(?P<value>.*)$"
)


def _strip_inline_comment(value: str) -> str:
    """Remove inline comments from an unquoted value."""
    match = re.search(r"\s+#.*$", value)
    if match:
        return value[: match.start()]
    return value


def _unquote(value: str) -> str:
    """Strip surrounding quotes and handle escape sequences."""
    if len(value) >= 2:
        if (value[0] == '"' and value[-1] == '"'):
            return bytes(value[1:-1], "utf-8").decode("unicode_escape")
        if (value[0] == "'" and value[-1] == "'"):
            return value[1:-1]
    return _strip_inline_comment(value).strip()


def parse_env_string(content: str) -> Dict[str, str]:
    """Parse a .env file content string into a dictionary.

    Args:
        content: Raw string contents of a .env file.

    Returns:
        A dict mapping variable names to their string values.
    """
    result: Dict[str, str] = {}
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = ENV_LINE_RE.match(stripped)
        if match:
            key = match.group("key")
            raw_value = match.group("value").strip()
            result[key] = _unquote(raw_value)
    return result


def parse_env_file(path: str) -> Dict[str, str]:
    """Read and parse a .env file from disk.

    Args:
        path: Filesystem path to the .env file.

    Returns:
        A dict mapping variable names to their string values.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    with open(path, "r", encoding="utf-8") as fh:
        return parse_env_string(fh.read())


def serialize_env(variables: Dict[str, str]) -> str:
    """Serialize a variable dict back to .env file format.

    Args:
        variables: Mapping of variable names to values.

    Returns:
        A string suitable for writing to a .env file.
    """
    lines = []
    for key, value in variables.items():
        if any(c in value for c in (" ", "#", "'", "\\")):
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'{key}="{escaped}"')
        else:
            lines.append(f"{key}={value}")
    return "\n".join(lines) + "\n"
