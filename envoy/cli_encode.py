"""CLI command: encode or decode .env values."""

from __future__ import annotations

import argparse
import sys

from envoy.encoder import EncoderError, decode_env, encode_env, list_schemes
from envoy.parser import parse_env_file, serialize_env
from envoy.sync import SyncError, load_local, save_local


def build_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs: dict = dict(
        prog="envoy encode",
        description="Encode or decode values in a .env file.",
    )
    parser = parent.add_parser("encode", **kwargs) if parent else argparse.ArgumentParser(**kwargs)
    parser.add_argument("file", help="Path to the .env file")
    parser.add_argument(
        "--scheme",
        default="base64",
        help=f"Encoding scheme. Choices: {', '.join(list_schemes())} (default: base64)",
    )
    parser.add_argument(
        "--decode",
        action="store_true",
        help="Decode values instead of encoding them",
    )
    parser.add_argument(
        "--keys",
        nargs="+",
        metavar="KEY",
        help="Only encode/decode these specific keys",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print result without writing to file",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print result to stdout instead of writing to file",
    )
    return parser


def run_encode(args: argparse.Namespace) -> int:
    try:
        env = load_local(args.file)
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        if args.decode:
            result = decode_env(env, args.scheme, keys=args.keys)
            action = "Decoded"
        else:
            result = encode_env(env, args.scheme, keys=args.keys)
            action = "Encoded"
    except EncoderError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    changed = [k for k in result if result[k] != env.get(k)]

    if args.dry_run or args.stdout:
        print(serialize_env(result))
        if not args.stdout:
            print(f"\n# {action} {len(changed)} key(s) (dry run — not written)")
        return 0

    try:
        save_local(args.file, result, overwrite=True)
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"{action} {len(changed)} key(s) in {args.file} using scheme '{args.scheme}'.")
    return 0
