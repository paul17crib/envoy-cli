"""CLI command: obfuscate — partially mask env values for safe sharing."""

import argparse
import sys
from envoy.sync import load_local, save_local, SyncError
from envoy.obfuscator import obfuscate_env, get_obfuscated_keys
from envoy.parser import serialize_env


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envoy obfuscate",
        description="Partially mask env values, revealing only the first N characters.",
    )
    p.add_argument("file", help="Path to the .env file")
    p.add_argument(
        "--keys", nargs="+", metavar="KEY",
        help="Keys to obfuscate (default: all keys)",
    )
    p.add_argument(
        "--reveal", type=int, default=4,
        help="Number of characters to reveal (default: 4)",
    )
    p.add_argument(
        "--scramble", action="store_true",
        help="Fully mask all characters, ignoring --reveal",
    )
    p.add_argument(
        "--mask-char", default="*", dest="mask_char",
        help="Character used for masking (default: *)",
    )
    p.add_argument(
        "--output", metavar="FILE",
        help="Write obfuscated output to this file instead of stdout",
    )
    p.add_argument(
        "--dry-run", action="store_true",
        help="Print what would be changed without writing",
    )
    return p


def run_obfuscate(args: argparse.Namespace) -> int:
    try:
        env = load_local(args.file)
    except SyncError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    try:
        obfuscated = obfuscate_env(
            env,
            keys=args.keys,
            reveal=args.reveal,
            mask_char=args.mask_char,
            scramble=args.scramble,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    changed = get_obfuscated_keys(env, obfuscated)

    if args.dry_run:
        if not changed:
            print("No keys would be obfuscated.")
        else:
            for key in changed:
                print(f"  {key}: {env[key]!r} -> {obfuscated[key]!r}")
        return 0

    serialized = serialize_env(obfuscated)

    if args.output:
        try:
            save_local(args.output, obfuscated, overwrite=True)
            print(f"Obfuscated {len(changed)} key(s) -> {args.output}")
        except SyncError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
    else:
        print(serialized, end="")

    return 0
