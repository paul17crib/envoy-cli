"""CLI command: envoy patch — apply a patch .env file onto a target .env file."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from envoy.parser import parse_env_file, serialize_env
from envoy.patcher import format_patch_report, patch_env
from envoy.sync import SyncError, load_local, save_local


def build_parser(parent: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:
    kwargs = dict(
        prog="envoy patch",
        description="Apply a patch .env file onto a target .env file.",
    )
    parser = parent.add_parser("patch", **kwargs) if parent else argparse.ArgumentParser(**kwargs)
    parser.add_argument("target", help="Target .env file to patch.")
    parser.add_argument("patch_file", help="Patch .env file containing updates.")
    parser.add_argument(
        "--no-add",
        action="store_true",
        help="Do not add keys that are absent from the target file.",
    )
    parser.add_argument(
        "--no-overwrite",
        action="store_true",
        help="Do not overwrite keys that already exist in the target file.",
    )
    parser.add_argument(
        "--keys",
        nargs="+",
        metavar="KEY",
        help="Only apply patch for these specific keys.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing anything.",
    )
    return parser


def run_patch(args: argparse.Namespace) -> int:
    try:
        base = load_local(args.target)
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        patch = load_local(args.patch_file)
    except SyncError as exc:
        print(f"error: patch file — {exc}", file=sys.stderr)
        return 1

    patched, report = patch_env(
        base,
        patch,
        add_new=not args.no_add,
        overwrite=not args.no_overwrite,
        keys=args.keys,
    )

    print(format_patch_report(report))

    if args.dry_run:
        print("(dry-run) No changes written.")
        return 0

    if report.total_changed == 0:
        return 0

    try:
        save_local(args.target, patched, overwrite=True)
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    return 0
