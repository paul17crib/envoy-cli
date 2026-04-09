import argparse
import sys

from envoy.sync import load_local, save_local, SyncError


def build_parser(subparsers=None):
    description = "Rename a key in a .env file"
    if subparsers is not None:
        parser = subparsers.add_parser("rename", help=description)
    else:
        parser = argparse.ArgumentParser(description=description)

    parser.add_argument("old_key", help="The existing key name")
    parser.add_argument("new_key", help="The new key name")
    parser.add_argument(
        "--file", "-f", default=".env", help="Path to the .env file (default: .env)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the rename without writing changes",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite new_key if it already exists",
    )
    return parser


def run_rename(args):
    try:
        env = load_local(args.file)
    except SyncError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    old_key = args.old_key
    new_key = args.new_key

    if old_key not in env:
        print(f"Error: key '{old_key}' not found in {args.file}", file=sys.stderr)
        return 1

    if new_key in env and not args.force:
        print(
            f"Error: key '{new_key}' already exists. Use --force to overwrite.",
            file=sys.stderr,
        )
        return 1

    value = env[old_key]

    # Preserve insertion order: rebuild dict with key renamed in place
    updated = {}
    for k, v in env.items():
        if k == old_key:
            updated[new_key] = value
        elif k == new_key and args.force:
            # Skip the old new_key entry; it was already inserted above
            continue
        else:
            updated[k] = v

    if args.dry_run:
        print(f"[dry-run] Would rename '{old_key}' -> '{new_key}' in {args.file}")
        print(f"  {new_key}={value}")
        return 0

    try:
        save_local(args.file, updated, overwrite=True)
    except SyncError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Renamed '{old_key}' -> '{new_key}' in {args.file}")
    return 0
