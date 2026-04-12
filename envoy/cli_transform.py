"""CLI command: envoy transform — apply value transformations to .env files."""

import argparse
import sys
from typing import List, Optional

from envoy.sync import load_local, save_local, SyncError
from envoy.transformer import transform_env, get_transformed_keys, TransformError, BUILTIN_TRANSFORMS
from envoy.masker import mask_env


def build_parser(subparsers=None) -> argparse.ArgumentParser:
    desc = "Apply value transformations to keys in a .env file."
    if subparsers is not None:
        parser = subparsers.add_parser("transform", help=desc, description=desc)
    else:
        parser = argparse.ArgumentParser(prog="envoy transform", description=desc)

    parser.add_argument("file", nargs="?", default=".env", help="Path to .env file")
    parser.add_argument(
        "--transform", "-t",
        dest="transforms",
        action="append",
        default=[],
        metavar="NAME",
        help=f"Transform to apply (repeatable). Available: {', '.join(sorted(BUILTIN_TRANSFORMS))}",
    )
    parser.add_argument(
        "--keys", "-k",
        nargs="+",
        default=None,
        metavar="KEY",
        help="Only transform these keys (default: all keys)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print result to stdout without writing the file",
    )
    parser.add_argument(
        "--mask",
        action="store_true",
        help="Mask sensitive values in dry-run output",
    )
    return parser


def run_transform(args: argparse.Namespace) -> int:
    try:
        env = load_local(args.file)
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not args.transforms:
        print("error: at least one --transform must be specified.", file=sys.stderr)
        return 1

    try:
        result = transform_env(env, args.transforms, keys=args.keys)
    except TransformError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    changed = get_transformed_keys(env, result)

    if args.dry_run:
        display = mask_env(result) if args.mask else result
        for key, value in display.items():
            print(f"{key}={value}")
        print(f"\n# {len(changed)} key(s) would be transformed.", file=sys.stderr)
        return 0

    save_local(args.file, result, overwrite=True)
    print(f"Transformed {len(changed)} key(s) in '{args.file}'.")
    return 0
