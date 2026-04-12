"""CLI command: envoy prompt — interactively fill missing keys in an env file."""

from __future__ import annotations

import argparse
import sys
from typing import List

from envoy.masker import is_sensitive_key
from envoy.prompter import PromptAborted, prompt_missing
from envoy.sync import SyncError, load_local, save_local


def build_parser(parent: argparse._SubParsersAction = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        prog="envoy prompt",
        description="Interactively fill in missing or empty values in an env file.",
    )
    parser = parent.add_parser("prompt", **kwargs) if parent else argparse.ArgumentParser(**kwargs)
    parser.add_argument("file", nargs="?", default=".env", help="Path to the .env file (default: .env)")
    parser.add_argument(
        "--keys",
        nargs="+",
        metavar="KEY",
        help="Specific keys to prompt for (default: all empty/missing keys)",
    )
    parser.add_argument(
        "--all",
        dest="prompt_all",
        action="store_true",
        help="Prompt for every key, not just empty ones",
    )
    parser.add_argument(
        "--no-overwrite",
        action="store_true",
        help="Skip keys that already have non-empty values",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resulting env without saving",
    )
    return parser


def run_prompt(args: argparse.Namespace) -> int:
    try:
        env = load_local(args.file)
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.keys:
        target_keys: List[str] = args.keys
    elif args.prompt_all:
        target_keys = list(env.keys())
    else:
        target_keys = [k for k, v in env.items() if v.strip() == ""]

    if args.no_overwrite:
        target_keys = [k for k in target_keys if env.get(k, "").strip() == ""]

    if not target_keys:
        print("Nothing to prompt — all keys already have values.")
        return 0

    sensitive = [k for k in target_keys if is_sensitive_key(k)]

    try:
        updated = prompt_missing(env, target_keys, sensitive_keys=sensitive)
    except PromptAborted as exc:
        print(f"\nAborted: {exc}", file=sys.stderr)
        return 1

    if args.dry_run:
        for key, value in updated.items():
            display = "***" if is_sensitive_key(key) else value
            print(f"{key}={display}")
        return 0

    save_local(args.file, updated, overwrite=True)
    print(f"Saved {len(target_keys)} key(s) to {args.file}")
    return 0
