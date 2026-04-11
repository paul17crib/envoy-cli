"""CLI command: normalize — standardize values in a .env file."""

import argparse
import sys
from pathlib import Path

from envoy.normalizer import normalize_env, get_normalized_keys
from envoy.sync import load_local, save_local, SyncError
from envoy.parser import serialize_env


def build_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Normalize values in a .env file (booleans, whitespace, key casing)."
    if subparsers is not None:
        parser = subparsers.add_parser("normalize", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envoy normalize", description=description)

    parser.add_argument("file", nargs="?", default=".env", help="Path to .env file (default: .env)")
    parser.add_argument("--no-booleans", action="store_true", help="Skip boolean normalization")
    parser.add_argument("--no-strip", action="store_true", help="Skip whitespace stripping")
    parser.add_argument("--uppercase-keys", action="store_true", help="Convert all keys to uppercase")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    parser.add_argument("--stdout", action="store_true", help="Print result to stdout instead of file")
    return parser


def run_normalize(args) -> int:
    path = Path(args.file)

    try:
        original = load_local(path)
    except SyncError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    normalized = normalize_env(
        original,
        fix_booleans=not args.no_booleans,
        strip_whitespace=not args.no_strip,
        uppercase_keys=args.uppercase_keys,
    )

    changed = get_normalized_keys(original, normalized)

    if not changed and not args.uppercase_keys:
        print("Nothing to normalize.")
        return 0

    if args.dry_run or args.stdout:
        if changed:
            print(f"Would normalize {len(changed)} value(s):")
            for key, new_val in changed.items():
                old_val = original.get(key, "")
                print(f"  {key}: {old_val!r} -> {new_val!r}")
        if args.stdout:
            print(serialize_env(normalized))
        return 0

    try:
        save_local(path, normalized, overwrite=True)
    except SyncError as e:
        print(f"Error saving file: {e}", file=sys.stderr)
        return 1

    print(f"Normalized {len(changed)} value(s) in {path}.")
    return 0
