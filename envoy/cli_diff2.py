"""CLI command: envoy diff2 — compare two local .env files using differ."""

import argparse
import sys
from typing import List

from envoy.differ import compute_diff, diff_summary
from envoy.masker import mask_env
from envoy.sync import load_local, SyncError


_COLORS = {
    "+": "\033[32m",  # green
    "-": "\033[31m",  # red
    "~": "\033[33m",  # yellow
    "=": "\033[90m",  # grey
}
_RESET = "\033[0m"


def build_parser(parent: argparse._SubParsersAction = None) -> argparse.ArgumentParser:
    kwargs = dict(description="Compare two .env files and show differences.")
    if parent:
        parser = parent.add_parser("diff2", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument("base", help="Base .env file")
    parser.add_argument("target", help="Target .env file to compare against base")
    parser.add_argument("--no-mask", action="store_true", help="Show secret values unmasked")
    parser.add_argument("--unchanged", action="store_true", help="Also show unchanged keys")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI color output")
    return parser


def _colorize(symbol: str, text: str, no_color: bool) -> str:
    if no_color or symbol not in _COLORS:
        return text
    return f"{_COLORS[symbol]}{text}{_RESET}"


def _format_entry(entry) -> str:
    """Format a single diff entry into a human-readable line.

    Args:
        entry: A DiffEntry with symbol, key, old_value, and new_value fields.

    Returns:
        A formatted string representing the diff line.
    """
    if entry.symbol == "+":
        return f"{entry.symbol} {entry.key}={entry.new_value}"
    elif entry.symbol == "-":
        return f"{entry.symbol} {entry.key}={entry.old_value}"
    elif entry.symbol == "~":
        return f"{entry.symbol} {entry.key}: {entry.old_value!r} -> {entry.new_value!r}"
    else:
        return f"{entry.symbol} {entry.key}={entry.old_value}"


def run_diff2(args: argparse.Namespace) -> int:
    try:
        base_env = load_local(args.base)
    except SyncError as e:
        print(f"Error loading base file: {e}", file=sys.stderr)
        return 1

    try:
        target_env = load_local(args.target)
    except SyncError as e:
        print(f"Error loading target file: {e}", file=sys.stderr)
        return 1

    if not args.no_mask:
        base_env = mask_env(base_env)
        target_env = mask_env(target_env)

    entries = compute_diff(base_env, target_env, include_unchanged=args.unchanged)

    if not entries:
        print("No differences found.")
        return 0

    for entry in entries:
        line = _format_entry(entry)
        print(_colorize(entry.symbol, line, args.no_color))

    added, removed, changed = diff_summary(entries)
    print(f"\nSummary: +{added} added, -{removed} removed, ~{changed} changed")
    return 0
