import argparse
import sys

from envoy.sync import load_local, SyncError
from envoy.masker import is_sensitive_key


def build_parser(subparsers=None):
    description = "Get the value of one or more keys from a .env file."
    if subparsers is not None:
        parser = subparsers.add_parser("get", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envoy get", description=description)

    parser.add_argument("keys", nargs="+", help="Key(s) to retrieve")
    parser.add_argument(
        "--file", "-f", default=".env", help="Path to the .env file (default: .env)"
    )
    parser.add_argument(
        "--no-mask",
        action="store_true",
        help="Reveal sensitive values instead of masking them",
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="Print values as shell export statements",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Print only the value(s), no labels",
    )
    return parser


def run_get(args, out=None):
    if out is None:
        out = sys.stdout

    try:
        env = load_local(args.file)
    except SyncError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    missing = [k for k in args.keys if k not in env]
    if missing:
        for key in missing:
            print(f"Error: key '{key}' not found in {args.file}", file=sys.stderr)
        return 1

    for key in args.keys:
        value = env[key]
        sensitive = is_sensitive_key(key)
        display_value = "***" if (sensitive and not args.no_mask) else value

        if args.export:
            print(f"export {key}={display_value}", file=out)
        elif args.quiet:
            print(display_value, file=out)
        else:
            print(f"{key}={display_value}", file=out)

    return 0
