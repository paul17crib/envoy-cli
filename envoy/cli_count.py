"""CLI command: count pattern occurrences in .env values."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from envoy.counter import CounterError, count_env, get_matching_keys, total_matches
from envoy.sync import SyncError, load_local


def build_parser(subparsers=None) -> argparse.ArgumentParser:
    desc = "Count occurrences of a pattern in .env values."
    if subparsers is not None:
        parser = subparsers.add_parser("count", help=desc)
    else:
        parser = argparse.ArgumentParser(prog="envoy count", description=desc)
    parser.add_argument("pattern", help="Pattern or substring to count.")
    parser.add_argument("--file", "-f", default=".env", help="Path to .env file.")
    parser.add_argument("--keys", nargs="+", metavar="KEY", help="Restrict to specific keys.")
    parser.add_argument("--regex", action="store_true", help="Treat pattern as a regex.")
    parser.add_argument("--case-sensitive", action="store_true", help="Case-sensitive matching.")
    parser.add_argument("--include-keys", action="store_true", help="Also search within key names.")
    parser.add_argument("--only-matches", action="store_true", help="Only show keys with matches.")
    parser.add_argument("--summary", action="store_true", help="Print only total match count.")
    return parser


def run_count(args, out=sys.stdout, err=sys.stderr) -> int:
    try:
        env = load_local(args.file)
    except SyncError as exc:
        print(f"error: {exc}", file=err)
        return 1

    try:
        results = count_env(
            env,
            args.pattern,
            keys=args.keys,
            regex=args.regex,
            case_sensitive=args.case_sensitive,
            include_keys=args.include_keys,
        )
    except CounterError as exc:
        print(f"error: {exc}", file=err)
        return 1

    if args.summary:
        print(total_matches(results), file=out)
        return 0

    displayed = [r for r in results if r.count > 0] if args.only_matches else results
    for r in displayed:
        print(f"{r.key}: {r.count}", file=out)

    print(f"total: {total_matches(results)}", file=out)
    return 0
