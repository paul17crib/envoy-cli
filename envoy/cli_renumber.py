"""CLI command: envoy renumber — compact gaps in indexed env keys."""

from __future__ import annotations

import argparse
import sys
from typing import List

from envoy.renumberer import RenumbererError, find_gaps, get_renumber_preview, renumber_prefix
from envoy.sync import SyncError, load_local, save_local


def build_parser(subparsers=None) -> argparse.ArgumentParser:
    desc = "Renumber indexed keys (e.g. ITEM_1, ITEM_3 -> ITEM_1, ITEM_2)."
    if subparsers is not None:
        parser = subparsers.add_parser("renumber", help=desc, description=desc)
    else:
        parser = argparse.ArgumentParser(prog="envoy renumber", description=desc)
    parser.add_argument("file", help="Path to the .env file")
    parser.add_argument("prefix", help="Key prefix to renumber (e.g. ITEM)")
    parser.add_argument(
        "--start", type=int, default=1, metavar="N",
        help="Starting index (default: 1)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would change without writing",
    )
    parser.add_argument(
        "--gaps-only", action="store_true",
        help="Only report gaps without renumbering",
    )
    return parser


def run_renumber(args: argparse.Namespace) -> int:
    try:
        env = load_local(args.file)
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.gaps_only:
        gaps = find_gaps(env, args.prefix)
        if gaps:
            print(f"Gaps found in '{args.prefix}': {gaps}")
        else:
            print(f"No gaps found in '{args.prefix}'.")
        return 0

    try:
        preview = get_renumber_preview(env, args.prefix, start=args.start)
        if not preview:
            print(f"No changes needed for prefix '{args.prefix}'.")
            return 0

        for old_key, new_key in preview:
            print(f"  {old_key} -> {new_key}")

        if args.dry_run:
            print(f"Dry run: {len(preview)} key(s) would be renamed.")
            return 0

        new_env = renumber_prefix(env, args.prefix, start=args.start)
        save_local(args.file, new_env, overwrite=True)
        print(f"Renumbered {len(preview)} key(s) in '{args.file}'.")
        return 0
    except RenumbererError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
