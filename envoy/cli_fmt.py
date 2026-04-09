"""cli_fmt.py — Format (normalize) a .env file in-place or to stdout."""

import argparse
import sys
from pathlib import Path

from envoy.parser import parse_env_file, serialize_env
from envoy.sync import SyncError


def build_parser(subparsers=None):
    description = "Normalize and format a .env file."
    if subparsers is not None:
        parser = subparsers.add_parser("fmt", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envoy fmt", description=description)

    parser.add_argument(
        "file",
        nargs="?",
        default=".env",
        help="Path to the .env file (default: .env)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit with non-zero status if the file would be changed (do not write).",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print formatted output to stdout instead of writing back to the file.",
    )
    parser.add_argument(
        "--sort",
        action="store_true",
        help="Sort keys alphabetically before writing.",
    )
    return parser


def run_fmt(args, stdout=None, stderr=None):
    out = stdout or sys.stdout
    err = stderr or sys.stderr

    path = Path(args.file)

    if not path.exists():
        err.write(f"[error] File not found: {path}\n")
        return 1

    try:
        env = parse_env_file(str(path))
    except SyncError as exc:
        err.write(f"[error] {exc}\n")
        return 1

    if args.sort:
        env = dict(sorted(env.items()))

    formatted = serialize_env(env)
    original = path.read_text(encoding="utf-8")

    if args.check:
        if formatted != original:
            err.write(f"[fmt] {path} would be reformatted\n")
            return 1
        out.write(f"[fmt] {path} is already formatted\n")
        return 0

    if args.stdout:
        out.write(formatted)
        return 0

    path.write_text(formatted, encoding="utf-8")
    if formatted != original:
        out.write(f"[fmt] Reformatted {path}\n")
    else:
        out.write(f"[fmt] {path} unchanged\n")
    return 0
