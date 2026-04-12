"""CLI command: envoy summarize — show a summary of a .env file."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from envoy.sync import load_local, SyncError
from envoy.summarizer import summarize, format_summary


def build_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Display a statistical summary of a .env file."
    if subparsers is not None:
        parser = subparsers.add_parser("summarize", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envoy summarize", description=description)

    parser.add_argument(
        "file",
        nargs="?",
        default=".env",
        help="Path to the .env file (default: .env)",
    )
    parser.add_argument(
        "--delimiter",
        default="_",
        help="Key prefix delimiter (default: _)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Output summary as JSON",
    )
    return parser


def run_summarize(args: argparse.Namespace, argv: Optional[List[str]] = None) -> int:
    try:
        env = load_local(args.file)
    except SyncError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    summary = summarize(env, delimiter=args.delimiter)

    if args.as_json:
        import json
        data = {
            "total": summary.total,
            "sensitive": summary.sensitive_count,
            "non_sensitive": summary.non_sensitive_count,
            "filled": summary.filled_count,
            "empty": summary.empty_count,
            "longest_key": summary.longest_key,
            "longest_value_key": summary.longest_value_key,
            "prefixes": summary.prefixes,
        }
        print(json.dumps(data, indent=2))
    else:
        for line in format_summary(summary):
            print(line)

    return 0


if __name__ == "__main__":
    _parser = build_parser()
    _args = _parser.parse_args()
    sys.exit(run_summarize(_args))
