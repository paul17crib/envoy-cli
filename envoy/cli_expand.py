"""CLI command: envoy expand — expand variable references in a .env file."""

from __future__ import annotations

import argparse
import sys

from envoy.expander import ExpansionError, expand_env, get_expanded_keys
from envoy.sync import SyncError, load_local, save_local
from envoy.parser import serialize_env


def build_parser(parent: argparse._SubParsersAction = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        prog="envoy expand",
        description="Expand $VAR / ${VAR} references within .env values.",
    )
    parser = (
        parent.add_parser("expand", **kwargs) if parent else argparse.ArgumentParser(**kwargs)
    )
    parser.add_argument("file", help="Path to the .env file")
    parser.add_argument(
        "--output", "-o", default=None,
        help="Write result to this file instead of overwriting source",
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="Fail if any variable reference cannot be resolved",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print expanded output without writing any file",
    )
    parser.add_argument(
        "--summary", action="store_true",
        help="Print a summary of which keys were expanded",
    )
    return parser


def run_expand(args: argparse.Namespace) -> int:
    try:
        original = load_local(args.file)
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        expanded = expand_env(original, strict=args.strict)
    except ExpansionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(serialize_env(expanded))
        return 0

    changed = get_expanded_keys(original, expanded)

    dest = args.output or args.file
    try:
        save_local(dest, expanded, overwrite=True)
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.summary:
        if changed:
            print(f"Expanded {len(changed)} key(s): {', '.join(sorted(changed))}")
        else:
            print("No variable references found — file unchanged.")

    return 0
