"""cli_squash.py — CLI command to squash duplicate keys from a .env file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envoy.squasher import squash_lines, format_squash_report


def build_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    kwargs = dict(
        prog="envoy squash",
        description="Remove duplicate keys from a .env file, keeping first or last occurrence.",
    )
    parser = parent.add_parser("squash", **kwargs) if parent else argparse.ArgumentParser(**kwargs)
    parser.add_argument("file", help="Path to the .env file")
    parser.add_argument(
        "--strategy",
        choices=["last", "first"],
        default="last",
        help="Which occurrence to keep when duplicates exist (default: last)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would change without modifying the file",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Write squashed output to stdout instead of back to the file",
    )
    return parser


def run_squash(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    raw_lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    squashed, removed = squash_lines(raw_lines, strategy=args.strategy)

    report = format_squash_report(removed, source=str(path))

    if args.dry_run:
        print(report)
        if removed:
            print("\n--- squashed output (dry-run) ---")
            print("".join(squashed), end="")
        return 0

    if args.stdout:
        print("".join(squashed), end="")
        return 0

    if removed:
        path.write_text("".join(squashed), encoding="utf-8")

    print(report)
    return 0
