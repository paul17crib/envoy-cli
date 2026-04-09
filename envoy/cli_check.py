"""CLI command: envoy check — verify that all keys in a reference .env file are present in a target .env file."""

import argparse
import sys

from envoy.sync import load_local, SyncError


def build_parser(subparsers=None):
    description = "Check that all keys from a reference .env file exist in a target .env file."
    if subparsers is not None:
        parser = subparsers.add_parser("check", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envoy check", description=description)

    parser.add_argument(
        "reference",
        help="Path to the reference .env file (e.g. .env.example).",
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".env",
        help="Path to the target .env file to check (default: .env).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Also fail if target contains keys not present in reference.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output; only use exit code.",
    )
    return parser


def run_check(args, out=None):
    import sys
    if out is None:
        out = sys.stdout

    try:
        reference = load_local(args.reference)
    except SyncError as e:
        print(f"[error] {e}", file=out)
        return 1

    try:
        target = load_local(args.target)
    except SyncError as e:
        print(f"[error] {e}", file=out)
        return 1

    ref_keys = set(reference.keys())
    tgt_keys = set(target.keys())

    missing = sorted(ref_keys - tgt_keys)
    extra = sorted(tgt_keys - ref_keys)

    issues = []

    for key in missing:
        issues.append(("missing", key))

    if args.strict:
        for key in extra:
            issues.append(("extra", key))

    if not issues:
        if not args.quiet:
            print(f"[ok] '{args.target}' satisfies all keys in '{args.reference}'.", file=out)
        return 0

    if not args.quiet:
        for kind, key in issues:
            symbol = "MISSING" if kind == "missing" else "EXTRA"
            print(f"  [{symbol}] {key}", file=out)
        print(f"\n{len(issues)} issue(s) found.", file=out)

    return 1
