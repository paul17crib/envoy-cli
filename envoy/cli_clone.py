import argparse
import sys
from pathlib import Path
from envoy.sync import load_local, save_local, SyncError
from envoy.masker import mask_env


def build_parser(subparsers=None):
    description = "Clone a .env file to a new location with optional key filtering"
    if subparsers:
        parser = subparsers.add_parser("clone", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envoy clone", description=description)

    parser.add_argument("source", help="Source .env file path")
    parser.add_argument("destination", help="Destination .env file path")
    parser.add_argument(
        "--keys",
        nargs="+",
        metavar="KEY",
        help="Only clone specific keys",
    )
    parser.add_argument(
        "--exclude",
        nargs="+",
        metavar="KEY",
        help="Exclude specific keys from clone",
    )
    parser.add_argument(
        "--mask",
        action="store_true",
        help="Mask sensitive values in the cloned file",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite destination if it already exists",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the cloned output without writing",
    )
    return parser


def run_clone(args, out=sys.stdout, err=sys.stderr):
    source = Path(args.source)
    destination = Path(args.destination)

    try:
        env = load_local(source)
    except SyncError as e:
        err.write(f"Error: {e}\n")
        return 1

    if args.keys:
        missing = [k for k in args.keys if k not in env]
        if missing:
            err.write(f"Error: keys not found in source: {', '.join(missing)}\n")
            return 1
        env = {k: v for k, v in env.items() if k in args.keys}

    if args.exclude:
        env = {k: v for k, v in env.items() if k not in args.exclude}

    if args.mask:
        env = mask_env(env)

    if args.dry_run:
        out.write(f"# Dry-run clone: {source} -> {destination}\n")
        for k, v in env.items():
            out.write(f"{k}={v}\n")
        return 0

    try:
        save_local(destination, env, overwrite=args.overwrite)
    except SyncError as e:
        err.write(f"Error: {e}\n")
        return 1

    out.write(f"Cloned {len(env)} key(s) from '{source}' to '{destination}'\n")
    return 0
