"""cli_keys.py — List all keys from a .env file, with optional filtering by prefix."""

import argparse
import sys

from envoy.sync import load_local, SyncError
from envoy.masker import is_sensitive_key


def build_parser(subparsers=None):
    description = "List all keys defined in a .env file."
    if subparsers:
        parser = subparsers.add_parser("keys", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envoy keys", description=description)

    parser.add_argument(
        "file",
        nargs="?",
        default=".env",
        help="Path to the .env file (default: .env)",
    )
    parser.add_argument(
        "--prefix",
        default=None,
        help="Only show keys that start with this prefix (case-insensitive)",
    )
    parser.add_argument(
        "--sensitive-only",
        action="store_true",
        help="Only show keys detected as sensitive",
    )
    parser.add_argument(
        "--count",
        action="store_true",
        help="Print only the number of matching keys",
    )
    parser.add_argument(
        "--no-header",
        action="store_true",
        help="Suppress the column header",
    )
    return parser


def run_keys(args, out=None):
    if out is None:
        out = sys.stdout

    try:
        env = load_local(args.file)
    except SyncError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    keys = list(env.keys())

    if args.prefix:
        prefix_lower = args.prefix.lower()
        keys = [k for k in keys if k.lower().startswith(prefix_lower)]

    if args.sensitive_only:
        keys = [k for k in keys if is_sensitive_key(k)]

    if args.count:
        print(len(keys), file=out)
        return 0

    if not keys:
        print("No keys found.", file=out)
        return 0

    if not args.no_header:
        print(f"{'KEY':<40}  {'SENSITIVE'}", file=out)
        print("-" * 50, file=out)

    for key in keys:
        sensitive_flag = "yes" if is_sensitive_key(key) else "no"
        print(f"{key:<40}  {sensitive_flag}", file=out)

    return 0
