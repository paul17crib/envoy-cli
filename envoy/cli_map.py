"""envoy cli-map — Show where keys are defined across multiple .env files."""

from __future__ import annotations

import argparse
import sys
from typing import List

from envoy.mapper import (
    MapperError,
    build_key_map,
    find_duplicates,
    find_unique,
    format_map_report,
    keys_in_all,
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envoy map",
        description="Map keys across multiple .env files.",
    )
    p.add_argument("files", nargs="+", metavar="FILE", help=".env files to inspect")
    p.add_argument(
        "--duplicates", action="store_true", help="Show only keys defined in more than one file"
    )
    p.add_argument(
        "--unique", action="store_true", help="Show only keys defined in exactly one file"
    )
    p.add_argument(
        "--all", dest="all_files", action="store_true",
        help="Show only keys present in every file"
    )
    p.add_argument(
        "--values", action="store_true", help="Include values in the report"
    )
    return p


def run_map(args: argparse.Namespace) -> int:
    try:
        key_map = build_key_map(args.files)
    except MapperError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.all_files:
        shared = keys_in_all(key_map, len(args.files))
        filtered = {k: key_map[k] for k in shared}
    elif args.duplicates:
        filtered = find_duplicates(key_map)
    elif args.unique:
        filtered = find_unique(key_map)
    else:
        filtered = key_map

    if not filtered:
        print("No keys matched.")
        return 0

    report = format_map_report(filtered, show_values=args.values)
    print(report)
    return 0
