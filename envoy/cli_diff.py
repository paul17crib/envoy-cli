"""CLI command for diffing local and remote .env files."""

import sys
from typing import Optional

from envoy.sync import load_local, diff_envs, SyncError
from envoy.remote import pull, FileRemoteProvider
from envoy.masker import mask_env


DELETE_COLOR = "\033[91m"  # red
ADD_COLOR = "\033[92m"    # green
CHANGE_COLOR = "\033[93m" # yellow
RESET = "\033[0m"


def _colorize(symbol: str, line: str) -> str:
    if symbol == "-":
        return f"{DELETE_COLOR}{line}{RESET}"
    elif symbol == "+":
        return f"{ADD_COLOR}{line}{RESET}"
    elif symbol == "~":
        return f"{CHANGE_COLOR}{line}{RESET}"
    return line


def print_diff(diff: dict, use_color: bool = True) -> None:
    """Pretty-print a diff dict produced by diff_envs."""
    if not diff:
        print("No differences found.")
        return

    for key, (status, local_val, remote_val) in sorted(diff.items()):
        if status == "added":
            line = f"+ {key}={remote_val}"
            print(_colorize("+", line) if use_color else line)
        elif status == "removed":
            line = f"- {key}={local_val}"
            print(_colorize("-", line) if use_color else line)
        elif status == "changed":
            old_line = f"~ {key}: {local_val!r} -> {remote_val!r}"
            print(_colorize("~", old_line) if use_color else old_line)


def run_diff(
    local_path: str,
    remote_path: str,
    mask_secrets: bool = True,
    no_color: bool = False,
    exit_nonzero: bool = False,
) -> int:
    """Run the diff command. Returns exit code."""
    try:
        local_env = load_local(local_path)
    except SyncError as e:
        print(f"Error loading local file: {e}", file=sys.stderr)
        return 1

    try:
        provider = FileRemoteProvider(remote_path)
        remote_env = pull(provider)
    except Exception as e:
        print(f"Error loading remote file: {e}", file=sys.stderr)
        return 1

    if mask_secrets:
        local_env = mask_env(local_env)
        remote_env = mask_env(remote_env)

    diff = diff_envs(local_env, remote_env)
    print_diff(diff, use_color=not no_color)

    if exit_nonzero and diff:
        return 2
    return 0
