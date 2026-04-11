"""CLI command: envoy mmerge — merge multiple .env files with conflict control."""

import argparse
import sys
from typing import List, Optional

from envoy.merger import MergeConflictError, find_conflicts, merge_all
from envoy.sync import load_local, save_local, SyncError


def build_parser(parent: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:
    desc = "Merge multiple .env files into one."
    if parent:
        p = parent.add_parser("mmerge", help=desc, description=desc)
    else:
        p = argparse.ArgumentParser(prog="envoy mmerge", description=desc)

    p.add_argument("sources", nargs="+", metavar="FILE", help="Source .env files (in order).")
    p.add_argument("-o", "--output", default=".env", help="Output file (default: .env).")
    p.add_argument(
        "--strategy",
        choices=["first", "last", "error"],
        default="last",
        help="Conflict resolution strategy (default: last).",
    )
    p.add_argument("--keys", nargs="+", metavar="KEY", help="Only include these keys.")
    p.add_argument("--dry-run", action="store_true", help="Print result without writing.")
    p.add_argument("--no-overwrite", action="store_true", help="Abort if output file exists.")
    p.add_argument("--show-conflicts", action="store_true", help="List conflicting keys and exit.")
    return p


def run_mmerge(args: argparse.Namespace) -> int:
    envs = []
    for path in args.sources:
        try:
            envs.append(load_local(path))
        except SyncError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    if args.show_conflicts:
        conflicts = find_conflicts(envs)
        if not conflicts:
            print("No conflicts found.")
            return 0
        for key, values in sorted(conflicts.items()):
            print(f"  {key}: {' | '.join(values)}")
        return 0

    try:
        merged = merge_all(envs, strategy=args.strategy, keys=args.keys or None)
    except MergeConflictError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.dry_run:
        for k, v in sorted(merged.items()):
            print(f"{k}={v}")
        return 0

    try:
        save_local(merged, args.output, overwrite=not args.no_overwrite)
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Merged {len(args.sources)} file(s) into '{args.output}' ({len(merged)} keys).")
    return 0
