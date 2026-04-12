"""cli_substitute.py — CLI command: envoy substitute."""

from __future__ import annotations

import argparse
import sys

from envoy.parser import parse_env_file, serialize_env
from envoy.substitutor import SubstitutionError, get_substituted_keys, substitute_env


def build_parser(parent: argparse._SubParsersAction = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        prog="envoy substitute",
        description="Replace values in a .env file using a find/replace pattern.",
    )
    parser = parent.add_parser("substitute", **kwargs) if parent else argparse.ArgumentParser(**kwargs)
    parser.add_argument("file", help="Path to the .env file")
    parser.add_argument("find", help="Value substring or regex pattern to find")
    parser.add_argument("replace", help="Replacement string")
    parser.add_argument("--keys", nargs="+", metavar="KEY", help="Restrict substitution to these keys")
    parser.add_argument("--regex", action="store_true", help="Treat FIND as a regular expression")
    parser.add_argument("--ignore-case", action="store_true", help="Case-insensitive matching")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without writing")
    parser.add_argument("--output", metavar="FILE", help="Write result to FILE instead of in-place")
    return parser


def run_substitute(args: argparse.Namespace) -> int:
    try:
        env = parse_env_file(args.file)
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 1

    try:
        updated = substitute_env(
            env,
            args.find,
            args.replace,
            keys=args.keys,
            regex=args.regex,
            case_sensitive=not args.ignore_case,
        )
    except SubstitutionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    changed = get_substituted_keys(env, updated)
    if not changed:
        print("No values were changed.")
        return 0

    for key in changed:
        print(f"  ~ {key}: {env[key]!r} -> {updated[key]!r}")

    if args.dry_run:
        print(f"\n(dry-run) {len(changed)} key(s) would be updated.")
        return 0

    dest = args.output or args.file
    content = serialize_env(updated)
    with open(dest, "w") as fh:
        fh.write(content)
    print(f"\n{len(changed)} key(s) updated -> {dest}")
    return 0
