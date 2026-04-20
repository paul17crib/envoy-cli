"""cli_freeze.py — CLI interface for freezing and thawing .env files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envoy.freezer import FreezeError, freeze_env, freeze_metadata, is_frozen, thaw_env
from envoy.parser import parse_env_file, serialize_env


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy freeze",
        description="Freeze or thaw .env files as immutable JSON snapshots.",
    )
    sub = parser.add_subparsers(dest="action", required=True)

    frz = sub.add_parser("freeze", help="Freeze an env file.")
    frz.add_argument("file", help="Source .env file.")
    frz.add_argument("--output", "-o", help="Output path (default: stdout).")
    frz.add_argument("--note", default="", help="Optional note to embed.")
    frz.add_argument("--keys", nargs="+", metavar="KEY", help="Only freeze these keys.")

    thw = sub.add_parser("thaw", help="Thaw a frozen env file back to .env format.")
    thw.add_argument("file", help="Frozen env file.")
    thw.add_argument("--output", "-o", help="Output path (default: stdout).")

    inf = sub.add_parser("info", help="Show metadata of a frozen env file.")
    inf.add_argument("file", help="Frozen env file.")

    return parser


def run_freeze(args: argparse.Namespace) -> int:
    if args.action == "freeze":
        path = Path(args.file)
        if not path.exists():
            print(f"Error: file not found: {args.file}", file=sys.stderr)
            return 1
        try:
            env = parse_env_file(str(path))
            result = freeze_env(env, note=args.note, keys=args.keys)
        except FreezeError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        if args.output:
            Path(args.output).write_text(result)
            print(f"Frozen: {args.output}")
        else:
            print(result)
        return 0

    if args.action == "thaw":
        path = Path(args.file)
        if not path.exists():
            print(f"Error: file not found: {args.file}", file=sys.stderr)
            return 1
        content = path.read_text()
        if not is_frozen(content):
            print("Error: file is not a frozen env snapshot.", file=sys.stderr)
            return 1
        try:
            env = thaw_env(content)
        except FreezeError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        output = serialize_env(env)
        if args.output:
            Path(args.output).write_text(output)
            print(f"Thawed: {args.output}")
        else:
            print(output)
        return 0

    if args.action == "info":
        path = Path(args.file)
        if not path.exists():
            print(f"Error: file not found: {args.file}", file=sys.stderr)
            return 1
        content = path.read_text()
        try:
            meta = freeze_metadata(content)
        except FreezeError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        import datetime
        ts = datetime.datetime.fromtimestamp(meta["frozen_at"]).isoformat()
        print(f"Frozen at : {ts}")
        print(f"Keys      : {meta['key_count']}")
        print(f"Note      : {meta['note'] or '(none)'}")
        print(f"Version   : {meta['version']}")
        return 0

    return 1
