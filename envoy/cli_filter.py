"""CLI command: envoy filter — filter .env entries by various criteria."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from envoy.filterer import (
    exclude_keys,
    filter_by_key_pattern,
    filter_by_value_pattern,
    filter_empty,
    filter_non_empty,
    filter_non_sensitive,
    filter_sensitive,
)
from envoy.parser import parse_env_file, serialize_env
from envoy.sync import SyncError, load_local


def build_parser(parent: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:
    kwargs = dict(
        prog="envoy filter",
        description="Filter .env entries by key/value pattern or sensitivity.",
    )
    parser = parent.add_parser("filter", **kwargs) if parent else argparse.ArgumentParser(**kwargs)
    parser.add_argument("file", nargs="?", default=".env", help="Source .env file (default: .env)")
    parser.add_argument("--key", metavar="PATTERN", help="Keep only keys matching this regex")
    parser.add_argument("--value", metavar="PATTERN", help="Keep only entries whose value matches this regex")
    parser.add_argument("--sensitive", action="store_true", help="Keep only sensitive keys")
    parser.add_argument("--non-sensitive", action="store_true", dest="non_sensitive", help="Keep only non-sensitive keys")
    parser.add_argument("--empty", action="store_true", help="Keep only entries with empty values")
    parser.add_argument("--non-empty", action="store_true", dest="non_empty", help="Keep only entries with non-empty values")
    parser.add_argument("--exclude", metavar="KEY", nargs="+", help="Exclude specific keys")
    parser.add_argument("--case-sensitive", action="store_true", dest="case_sensitive", help="Make pattern matching case-sensitive")
    parser.add_argument("--output", "-o", metavar="FILE", help="Write result to FILE instead of stdout")
    return parser


def run_filter(args: argparse.Namespace) -> int:
    try:
        env = load_local(args.file)
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    result = dict(env)

    if args.key:
        result = filter_by_key_pattern(result, args.key, case_sensitive=args.case_sensitive)
    if args.value:
        result = filter_by_value_pattern(result, args.value, case_sensitive=args.case_sensitive)
    if args.sensitive:
        result = filter_sensitive(result)
    if args.non_sensitive:
        result = filter_non_sensitive(result)
    if args.empty:
        result = filter_empty(result)
    if args.non_empty:
        result = filter_non_empty(result)
    if args.exclude:
        result = exclude_keys(result, args.exclude, case_sensitive=args.case_sensitive)

    output = serialize_env(result)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as fh:
                fh.write(output)
            print(f"Wrote {len(result)} entries to {args.output}")
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
    else:
        print(output, end="")

    return 0
