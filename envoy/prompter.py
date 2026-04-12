"""Interactive prompting utilities for envoy-cli.

Provides helpers to prompt users for missing env values,
confirmations, and secret input without echoing to terminal.
"""

from __future__ import annotations

import getpass
import sys
from typing import Dict, List, Optional


class PromptAborted(Exception):
    """Raised when the user aborts an interactive prompt session."""


def prompt_value(key: str, secret: bool = False, default: Optional[str] = None) -> str:
    """Prompt the user for a single env value.

    Args:
        key: The env key being requested.
        secret: If True, use getpass so input is not echoed.
        default: Optional default value shown in the prompt.

    Returns:
        The entered value (stripped), or the default if nothing entered.

    Raises:
        PromptAborted: If the user sends EOF (Ctrl+D).
    """
    label = f"{key}" + (f" [{default}]" if default is not None else "")
    try:
        if secret:
            value = getpass.getpass(f"{label} (hidden): ")
        else:
            value = input(f"{label}: ")
    except EOFError:
        raise PromptAborted(f"Prompt aborted by user at key '{key}'.")

    value = value.strip()
    if value == "" and default is not None:
        return default
    return value


def prompt_missing(env: Dict[str, str], keys: List[str], sensitive_keys: Optional[List[str]] = None) -> Dict[str, str]:
    """Prompt the user to fill in values for a list of missing keys.

    Args:
        env: Existing env dict to update (not mutated).
        keys: Keys that need to be filled in.
        sensitive_keys: Keys whose values should be hidden during input.

    Returns:
        A new dict with the original values plus the prompted ones.
    """
    sensitive_keys = sensitive_keys or []
    result = dict(env)
    for key in keys:
        is_secret = key in sensitive_keys
        value = prompt_value(key, secret=is_secret, default=result.get(key))
        result[key] = value
    return result


def confirm(message: str, default: bool = False) -> bool:
    """Ask the user a yes/no question.

    Args:
        message: The question to display.
        default: Default answer if user just presses Enter.

    Returns:
        True if the user confirmed, False otherwise.

    Raises:
        PromptAborted: If the user sends EOF.
    """
    hint = "[Y/n]" if default else "[y/N]"
    try:
        answer = input(f"{message} {hint}: ").strip().lower()
    except EOFError:
        raise PromptAborted("Confirmation aborted by user.")

    if answer == "":
        return default
    return answer in ("y", "yes")
