"""CLI command: envoy rename-bulk — bulk rename keys via prefix swap or JSON mapping."""

from __future__ import annotations

import argparse
import json
import sys

from envoy.renamer_bulk import BulkRenameError, rename_by_mapping, rename_prefix
from envoy.sync import SyncError, load_local, save_local


def build_parser(parent: argparse._SubParsersAction = None) -> argparse.ArgumentParser:
    desc = "Bulk rename keys in a .env file."
    if parent is not None:
        p = parent.add_parser("rename-bulk", help=desc)
    else:
        p = argparse.ArgumentParser(prog="envoy rename-bulk", description=desc)

    p.add_argument("file", help="Path to the .env file")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--prefix",
        nargs=2,
        metavar=("OLD", "NEW"),
        help="Replace OLD prefix with NEW prefix on all matching keys",
    )
    mode.add_argument(
        "--mapping",
        metavar="JSON",
        help='JSON object mapping old key names to new key names, e.g. \'{"A":"B"}\'',
    )
    p.add_argument("--overwrite", action="store_true", help="Allow overwriting existing target keys")
    p.add_argument("--dry-run", action="store_true", help="Print result without writing")
    return p


def run_rename_bulk(args: argparse.Namespace) -> int:
    try:
        env = load_local(args.file)
    except SyncError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    try:
        if args.prefix:
            old_prefix, new_prefix = args.prefix
            updated = rename_prefix(env, old_prefix, new_prefix, overwrite=args.overwrite)
        else:
            try:
                mapping = json.loads(args.mapping)
            except json.JSONDecodeError as exc:
                print(f"Error: invalid JSON mapping — {exc}", file=sys.stderr)
                return 1
            updated = rename_by_mapping(env, mapping, overwrite=args.overwrite)
    except BulkRenameError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    changed = [k for k in updated if k not in env] + [k for k in env if k not in updated]
    if not changed:
        print("No keys renamed.")

    if args.dry_run:
        for key, value in updated.items():
            print(f"{key}={value}")
        return 0

    try:
        save_local(args.file, updated, overwrite=True)
    except SyncError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Renamed {len(changed)} key(s) in '{args.file}'.")
    return 0
