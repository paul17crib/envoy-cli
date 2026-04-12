"""CLI command: envoy tokenize — split env values into tokens."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from envoy.sync import SyncError, load_local
from envoy.tokenizer import TokenizerError, get_token_counts, tokenize_env


def build_parser(parent: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:
    description = "Split env values into tokens and display results."
    if parent is not None:
        parser = parent.add_parser("tokenize", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envoy tokenize", description=description)

    parser.add_argument("file", nargs="?", default=".env", help="Env file to read (default: .env)")
    parser.add_argument("-k", "--keys", nargs="+", metavar="KEY", help="Only tokenize these keys")
    parser.add_argument("-d", "--delimiter", default=None, help="Literal delimiter to split on")
    parser.add_argument("-p", "--pattern", default=None, help="Regex pattern to split on")
    parser.add_argument("--counts", action="store_true", help="Show token counts only")
    return parser


def run_tokenize(args: argparse.Namespace) -> int:
    try:
        env = load_local(args.file)
    except SyncError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    try:
        results = tokenize_env(
            env,
            keys=args.keys,
            delimiter=args.delimiter,
            pattern=args.pattern,
        )
    except TokenizerError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not results:
        print("No keys to tokenize.")
        return 0

    if args.counts:
        counts = get_token_counts(results)
        for key, count in counts.items():
            print(f"{key}: {count} token(s)")
    else:
        for key, result in results.items():
            tokens_display = ", ".join(repr(t) for t in result.tokens)
            print(f"{key} ({result.count()}): [{tokens_display}]")

    return 0
