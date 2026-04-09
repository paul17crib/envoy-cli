"""cli_list.py — List all keys in a .env file, with optional filtering and masking."""

import argparse
from envoy.sync import load_local, SyncError
from envoy.masker import mask_env
from envoy.display import format_env_table


def build_parser(subparsers=None):
    description = "List all keys (and optionally values) in a .env file."
    if subparsers is not None:
        parser = subparsers.add_parser("list", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envoy list", description=description)

    parser.add_argument(
        "--file", "-f",
        default=".env",
        help="Path to the .env file (default: .env)",
    )
    parser.add_argument(
        "--keys-only",
        action="store_true",
        help="Print only key names, one per line.",
    )
    parser.add_argument(
        "--no-mask",
        action="store_true",
        help="Reveal sensitive values instead of masking them.",
    )
    parser.add_argument(
        "--prefix",
        default=None,
        help="Filter keys that start with the given prefix.",
    )
    return parser


def run_list(args, out=None):
    import sys
    if out is None:
        out = sys.stdout

    try:
        env = load_local(args.file)
    except SyncError as e:
        print(f"Error: {e}", file=out)
        return 1

    if args.prefix:
        env = {k: v for k, v in env.items() if k.startswith(args.prefix)}

    if not env:
        print("No keys found.", file=out)
        return 0

    if args.keys_only:
        for key in sorted(env.keys()):
            print(key, file=out)
        return 0

    display_env = env if args.no_mask else mask_env(env)
    table = format_env_table(display_env)
    print(table, file=out)
    return 0
