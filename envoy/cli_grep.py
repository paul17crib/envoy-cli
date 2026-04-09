import argparse
import sys
import re

from envoy.sync import load_local, SyncError
from envoy.masker import mask_env


def build_parser(subparsers=None):
    description = "Search for keys or values matching a pattern in a .env file."
    if subparsers is not None:
        parser = subparsers.add_parser("grep", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envoy grep", description=description)

    parser.add_argument("pattern", help="Regex pattern to search for")
    parser.add_argument(
        "--file", "-f", default=".env", help="Path to the .env file (default: .env)"
    )
    parser.add_argument(
        "--keys-only", action="store_true", help="Only search in key names"
    )
    parser.add_argument(
        "--values-only", action="store_true", help="Only search in values"
    )
    parser.add_argument(
        "--no-mask", action="store_true", help="Do not mask sensitive values in output"
    )
    parser.add_argument(
        "--ignore-case", "-i", action="store_true", help="Case-insensitive matching"
    )
    parser.add_argument(
        "--count", "-c", action="store_true", help="Print only the count of matching entries"
    )
    return parser


def run_grep(args, out=None):
    if out is None:
        out = sys.stdout

    try:
        env = load_local(args.file)
    except SyncError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    flags = re.IGNORECASE if args.ignore_case else 0
    try:
        pattern = re.compile(args.pattern, flags)
    except re.error as e:
        print(f"Error: Invalid regex pattern: {e}", file=sys.stderr)
        return 1

    display_env = env if args.no_mask else mask_env(env)

    matches = []
    for key, value in env.items():
        match_key = not args.values_only and pattern.search(key)
        match_value = not args.keys_only and pattern.search(value)
        if match_key or match_value:
            matches.append(key)

    if args.count:
        print(len(matches), file=out)
        return 0

    if not matches:
        return 1

    for key in matches:
        print(f"{key}={display_env[key]}", file=out)

    return 0
