"""CLI command: envoy swap — exchange values (or names) of two env keys."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from envoy.parser import parse_env_file, serialize_env
from envoy.sync import save_local
from envoy.swapper import SwapError, get_swap_preview, swap_keys, swap_names


def build_parser(sub: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:
    desc = "Swap the values (or names) of two keys in an env file."
    if sub is not None:
        p = sub.add_parser("swap", help=desc, description=desc)
    else:
        p = argparse.ArgumentParser(prog="envoy swap", description=desc)
    p.add_argument("file", help="Path to the .env file")
    p.add_argument("key_a", help="First key")
    p.add_argument("key_b", help="Second key")
    p.add_argument(
        "--names",
        action="store_true",
        help="Swap the key names rather than the values",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would change without writing the file",
    )
    p.add_argument(
        "--no-overwrite",
        action="store_true",
        help="Do not overwrite the original file (implies --dry-run output)",
    )
    return p


def run_swap(args: argparse.Namespace) -> int:
    try:
        env = parse_env_file(args.file)
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 1

    try:
        if args.names:
            new_env = swap_names(env, args.key_a, args.key_b)
        else:
            new_env = swap_keys(env, args.key_a, args.key_b)
    except SwapError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    preview = get_swap_preview(env, args.key_a, args.key_b)
    for key, change in preview.items():
        print(f"  {key}: {change['before']!r} -> {change['after']!r}")

    if args.dry_run or args.no_overwrite:
        print("(dry run — no changes written)")
        return 0

    save_local(args.file, new_env, overwrite=True)
    print(f"Swapped {args.key_a!r} and {args.key_b!r} in {args.file}")
    return 0
