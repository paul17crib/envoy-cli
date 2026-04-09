import argparse
import sys
from envoy.sync import load_local, save_local, SyncError


def build_parser(subparsers=None):
    description = "Remove one or more keys from a .env file"
    if subparsers:
        parser = subparsers.add_parser("unset", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envoy unset", description=description)

    parser.add_argument(
        "keys",
        nargs="+",
        metavar="KEY",
        help="One or more keys to remove from the env file",
    )
    parser.add_argument(
        "--file",
        "-f",
        default=".env",
        help="Path to the .env file (default: .env)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without writing changes",
    )
    parser.add_argument(
        "--ignore-missing",
        action="store_true",
        help="Do not error if a key does not exist in the file",
    )
    return parser


def run_unset(args, out=None, err=None):
    if out is None:
        out = sys.stdout
    if err is None:
        err = sys.stderr

    try:
        env = load_local(args.file)
    except SyncError as e:
        err.write(f"Error: {e}\n")
        return 1

    removed = []
    missing = []

    for key in args.keys:
        if key in env:
            removed.append(key)
        else:
            missing.append(key)

    if missing and not args.ignore_missing:
        for key in missing:
            err.write(f"Error: Key '{key}' not found in {args.file}\n")
        return 1

    if missing and args.ignore_missing:
        for key in missing:
            out.write(f"Warning: Key '{key}' not found in {args.file}, skipping\n")

    if not removed:
        out.write("No keys to remove.\n")
        return 0

    if args.dry_run:
        out.write(f"Dry run — would remove from {args.file}:\n")
        for key in removed:
            out.write(f"  - {key}\n")
        return 0

    updated = {k: v for k, v in env.items() if k not in removed}

    try:
        save_local(args.file, updated, overwrite=True)
    except SyncError as e:
        err.write(f"Error: {e}\n")
        return 1

    for key in removed:
        out.write(f"Removed '{key}' from {args.file}\n")

    return 0
