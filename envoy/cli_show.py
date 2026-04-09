"""CLI command for displaying .env file contents with optional secret masking."""

import argparse
import sys

from envoy.sync import load_local, SyncError
from envoy.masker import mask_env, get_masked_keys
from envoy.display import format_env_table, summarize_env
from envoy.validator import validate_env, has_errors, format_issues


def build_parser(subparsers=None):
    description = "Display the contents of a .env file."
    if subparsers is not None:
        parser = subparsers.add_parser("show", help=description, description=description)
    else:
        parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "file",
        nargs="?",
        default=".env",
        help="Path to the .env file (default: .env)",
    )
    parser.add_argument(
        "--no-mask",
        action="store_true",
        default=False,
        help="Show sensitive values in plain text (default: mask them)",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        default=False,
        help="Print a one-line summary instead of the full table",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        default=False,
        help="Run validation and show any issues below the table",
    )
    parser.add_argument(
        "--keys",
        nargs="+",
        metavar="KEY",
        default=None,
        help="Only display the specified keys",
    )
    return parser


def run_show(args, out=sys.stdout, err=sys.stderr):
    try:
        env = load_local(args.file)
    except SyncError as exc:
        print(f"Error: {exc}", file=err)
        return 1

    if args.keys:
        missing = [k for k in args.keys if k not in env]
        if missing:
            print(f"Warning: keys not found: {', '.join(missing)}", file=err)
        env = {k: v for k, v in env.items() if k in args.keys}

    display_env = env if args.no_mask else mask_env(env)

    if args.summary:
        masked_keys = [] if args.no_mask else get_masked_keys(env)
        print(summarize_env(display_env, masked_keys=masked_keys), file=out)
    else:
        print(format_env_table(display_env), file=out)

    if args.validate:
        issues = validate_env(env)
        if issues:
            print("", file=out)
            print(format_issues(issues), file=out)
            if has_errors(issues):
                return 2

    return 0
