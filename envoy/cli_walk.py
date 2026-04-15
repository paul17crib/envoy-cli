"""CLI command: walk a directory and list discovered .env files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envoy.walker import WalkerError, collect_env_files, summarize_walk


def build_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # noqa: E501
    kwargs = dict(
        prog="envoy walk",
        description="Discover .env files under a directory tree.",
    )
    if parent is not None:
        parser = parent.add_parser("walk", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Root directory to walk (default: current directory).",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=10,
        metavar="N",
        help="Maximum recursion depth (default: 10).",
    )
    parser.add_argument(
        "--pattern",
        action="append",
        dest="patterns",
        metavar="PATTERN",
        help="Filename pattern to match; may be repeated.",
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        default=False,
        help="Include hidden directories (names starting with '.').",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        default=False,
        help="Print a summary line instead of individual paths.",
    )
    return parser


def run_walk(args: argparse.Namespace) -> int:
    root = Path(args.root)
    patterns = args.patterns or None
    skip_hidden = not args.include_hidden

    try:
        if args.summary:
            info = summarize_walk(
                root,
                patterns=patterns,
                max_depth=args.max_depth,
                skip_hidden=skip_hidden,
            )
            print(f"Root : {info['root']}")
            print(f"Files: {info['total_files']}")
            print(f"Dirs : {info['total_dirs']}")
            for f in info["files"]:
                print(f"  {f}")
        else:
            files = collect_env_files(
                root,
                patterns=patterns,
                max_depth=args.max_depth,
                skip_hidden=skip_hidden,
            )
            if not files:
                print("No .env files found.", file=sys.stderr)
                return 1
            for f in files:
                print(f)
    except WalkerError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0
