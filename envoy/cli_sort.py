import argparse
import sys

from envoy.sync import load_local, save_local, SyncError
from envoy.parser import serialize_env


def build_parser(subparsers=None):
    description = "Sort keys in a .env file alphabetically."
    if subparsers is not None:
        parser = subparsers.add_parser("sort", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envoy sort", description=description)

    parser.add_argument(
        "file",
        nargs="?",
        default=".env",
        help="Path to the .env file (default: .env)",
    )
    parser.add_argument(
        "--reverse",
        action="store_true",
        help="Sort keys in reverse (descending) order.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print sorted output without modifying the file.",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print sorted output to stdout instead of writing to file.",
    )
    return parser


def run_sort(args, out=None):
    if out is None:
        out = sys.stdout

    try:
        env = load_local(args.file)
    except SyncError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    sorted_env = dict(sorted(env.items(), reverse=args.reverse))
    serialized = serialize_env(sorted_env)

    if args.dry_run or args.stdout:
        print(serialized, file=out, end="")
        if args.dry_run:
            print(f"[dry-run] Would write {len(sorted_env)} keys to {args.file}", file=out)
        return 0

    try:
        save_local(args.file, sorted_env, overwrite=True)
    except SyncError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Sorted {len(sorted_env)} keys in {args.file}", file=out)
    return 0
