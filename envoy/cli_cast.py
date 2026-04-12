"""CLI command: envoy cast — cast env values to a target type."""

import argparse
import sys
from typing import Optional

from envoy.caster import cast_env, cast_back, list_types, CastError
from envoy.sync import load_local, save_local, SyncError


def build_parser(subparsers=None):
    desc = "Cast env values to a target type (int, float, bool, list, str)."
    if subparsers is not None:
        p = subparsers.add_parser("cast", help=desc, description=desc)
    else:
        p = argparse.ArgumentParser(prog="envoy cast", description=desc)
    p.add_argument("type", choices=list_types(), help="Target type to cast to")
    p.add_argument("--file", "-f", default=".env", help="Path to .env file")
    p.add_argument("--keys", "-k", nargs="+", help="Specific keys to cast (default: all)")
    p.add_argument("--delimiter", "-d", default=",", help="Delimiter for list type (default: ,)")
    p.add_argument("--dry-run", action="store_true", help="Print result without writing")
    p.add_argument("--output", "-o", help="Write result to this file instead")
    return p


def run_cast(args, out=sys.stdout, err=sys.stderr) -> int:
    try:
        env = load_local(args.file)
    except SyncError as exc:
        print(f"Error: {exc}", file=err)
        return 1

    try:
        typed = cast_env(env, args.type, keys=args.keys, delimiter=args.delimiter)
    except CastError as exc:
        print(f"Cast error: {exc}", file=err)
        return 1

    # Convert all values back to strings for storage
    result = {k: cast_back(v) for k, v in typed.items()}

    if args.dry_run:
        for key, val in result.items():
            if env.get(key) != val:
                print(f"{key}={val}", file=out)
        return 0

    dest = args.output or args.file
    try:
        save_local(dest, result, overwrite=True)
    except SyncError as exc:
        print(f"Error: {exc}", file=err)
        return 1

    changed = sum(1 for k, v in result.items() if env.get(k) != v)
    print(f"Cast {changed} value(s) to '{args.type}' in {dest}", file=out)
    return 0
