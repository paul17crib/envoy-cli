"""CLI command: envoy sort2 — sort .env file keys with multiple strategies."""

import argparse
import sys
from pathlib import Path

from envoy.parser import parse_env_file, serialize_env
from envoy.sorter import sort_env, sort_by_value, sort_by_length, group_sort


def build_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Sort keys in a .env file using various strategies."
    if subparsers:
        parser = subparsers.add_parser("sort2", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envoy sort2", description=description)

    parser.add_argument("file", nargs="?", default=".env", help="Path to .env file")
    parser.add_argument(
        "--by",
        choices=["key", "value", "length", "group"],
        default="key",
        help="Sort strategy (default: key)",
    )
    parser.add_argument("--reverse", action="store_true", help="Sort in descending order")
    parser.add_argument(
        "--case-sensitive", action="store_true", help="Use case-sensitive comparison"
    )
    parser.add_argument(
        "--delimiter",
        default="_",
        help="Delimiter for group sort (default: _)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print result without writing to file",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Write output to stdout instead of file",
    )
    return parser


def run_sort2(args) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"[error] File not found: {path}", file=sys.stderr)
        return 1

    env = parse_env_file(str(path))

    strategy = getattr(args, "by", "key")
    reverse = getattr(args, "reverse", False)
    case_sensitive = getattr(args, "case_sensitive", False)
    delimiter = getattr(args, "delimiter", "_")

    if strategy == "key":
        sorted_env = sort_env(env, reverse=reverse, case_sensitive=case_sensitive)
    elif strategy == "value":
        sorted_env = sort_by_value(env, reverse=reverse, case_sensitive=case_sensitive)
    elif strategy == "length":
        sorted_env = sort_by_length(env, reverse=reverse)
    elif strategy == "group":
        sorted_env = group_sort(env, delimiter=delimiter, reverse=reverse)
    else:
        print(f"[error] Unknown sort strategy: {strategy}", file=sys.stderr)
        return 1

    output = serialize_env(sorted_env)

    if args.dry_run or args.stdout:
        print(output, end="")
        return 0

    path.write_text(output, encoding="utf-8")
    print(f"[ok] Sorted {len(sorted_env)} keys in {path} (strategy={strategy})")
    return 0
