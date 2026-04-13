"""CLI command: envoy truncate — truncate or pad env values by length."""

from __future__ import annotations

import argparse
import sys

from envoy.sync import load_local, save_local, SyncError
from envoy.truncator import TruncateError, truncate_env, pad_env, get_truncated_keys


def build_parser(subparsers=None) -> argparse.ArgumentParser:
    desc = "Truncate or pad values in a .env file by length constraints."
    if subparsers is not None:
        parser = subparsers.add_parser("truncate", help=desc, description=desc)
    else:
        parser = argparse.ArgumentParser(prog="envoy truncate", description=desc)

    parser.add_argument("file", help="Path to the .env file")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--max-length", type=int, metavar="N",
        help="Truncate values longer than N characters",
    )
    mode.add_argument(
        "--min-length", type=int, metavar="N",
        help="Pad values shorter than N characters",
    )
    parser.add_argument(
        "--suffix", default="...",
        help="Suffix appended to truncated values (default: '...')",
    )
    parser.add_argument(
        "--pad-char", default=" ", metavar="CHAR",
        help="Character used for padding (default: space)",
    )
    parser.add_argument(
        "--align", choices=["left", "right", "center"], default="left",
        help="Padding alignment (default: left)",
    )
    parser.add_argument(
        "--keys", nargs="+", metavar="KEY",
        help="Restrict operation to specific keys",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print result without writing to file",
    )
    parser.add_argument(
        "--stdout", action="store_true",
        help="Write output to stdout instead of file",
    )
    return parser


def run_truncate(args: argparse.Namespace) -> int:
    try:
        env = load_local(args.file)
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        if args.max_length is not None:
            affected = get_truncated_keys(env, args.max_length, args.keys)
            result = truncate_env(env, args.max_length, args.suffix, args.keys)
            operation = f"truncated to {args.max_length} chars"
        else:
            affected = [
                k for k in (args.keys or env)
                if k in env and len(env[k]) < args.min_length
            ]
            result = pad_env(env, args.min_length, args.pad_char, args.align, args.keys)
            operation = f"padded to {args.min_length} chars"
    except TruncateError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not affected:
        print("No values required changes.")
        return 0

    print(f"{len(affected)} key(s) {operation}: {', '.join(affected)}")

    if args.dry_run or args.stdout:
        from envoy.parser import serialize_env
        print(serialize_env(result))
        return 0

    try:
        save_local(args.file, result, overwrite=True)
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Updated {args.file}")
    return 0
