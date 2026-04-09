import argparse
import sys

from envoy.sync import load_local, save_local, SyncError
from envoy.masker import mask_env
from envoy.display import format_env_table


def build_parser(subparsers=None):
    description = "Copy keys from one .env file to another."
    if subparsers is not None:
        parser = subparsers.add_parser("copy", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envoy copy", description=description)

    parser.add_argument("source", help="Source .env file path")
    parser.add_argument("destination", help="Destination .env file path")
    parser.add_argument(
        "--keys",
        nargs="+",
        metavar="KEY",
        help="Specific keys to copy (copies all if omitted)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing keys in destination",
    )
    parser.add_argument(
        "--create",
        action="store_true",
        help="Create destination file if it does not exist",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing to destination",
    )
    parser.add_argument(
        "--no-mask",
        action="store_true",
        help="Show sensitive values in dry-run output",
    )
    return parser


def run_copy(args, out=None):
    if out is None:
        out = sys.stdout

    try:
        source_env = load_local(args.source)
    except SyncError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.keys:
        missing = [k for k in args.keys if k not in source_env]
        if missing:
            print(f"Error: Keys not found in source: {', '.join(missing)}", file=sys.stderr)
            return 1
        to_copy = {k: source_env[k] for k in args.keys}
    else:
        to_copy = dict(source_env)

    try:
        dest_env = load_local(args.destination)
    except SyncError:
        if args.create:
            dest_env = {}
        else:
            print(
                f"Error: Destination '{args.destination}' not found. Use --create to create it.",
                file=sys.stderr,
            )
            return 1

    skipped = []
    merged = dict(dest_env)
    for key, value in to_copy.items():
        if key in merged and not args.overwrite:
            skipped.append(key)
        else:
            merged[key] = value

    if skipped:
        print(f"Skipped existing keys (use --overwrite): {', '.join(skipped)}", file=out)

    if args.dry_run:
        display = merged if args.no_mask else mask_env(merged)
        print(format_env_table(display), file=out)
        print("Dry run complete. No changes written.", file=out)
        return 0

    save_local(args.destination, merged, overwrite=True)
    copied = [k for k in to_copy if k not in skipped]
    print(f"Copied {len(copied)} key(s) to '{args.destination}'.", file=out)
    return 0
