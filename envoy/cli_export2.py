"""CLI command: envoy export2 — export env vars to shell-friendly formats."""

from __future__ import annotations

import argparse
import sys

from envoy.exporter import ExportError, export_env, list_schemes
from envoy.sync import SyncError, load_local


def build_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    description = "Export .env variables to shell-friendly formats."
    if parent is not None:
        parser = parent.add_parser("export2", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envoy export2", description=description)

    parser.add_argument("file", nargs="?", default=".env", help="Source .env file (default: .env)")
    parser.add_argument(
        "--scheme",
        choices=list_schemes(),
        default="shell",
        help="Export format scheme (default: shell)",
    )
    parser.add_argument(
        "--mask",
        action="store_true",
        default=False,
        help="Mask sensitive values in output",
    )
    parser.add_argument(
        "--keys",
        nargs="+",
        metavar="KEY",
        default=None,
        help="Only export specific keys",
    )
    return parser


def run_export2(args: argparse.Namespace) -> int:
    try:
        env = load_local(args.file)
    except SyncError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.keys:
        missing = [k for k in args.keys if k not in env]
        if missing:
            print(f"Error: keys not found: {', '.join(missing)}", file=sys.stderr)
            return 1
        env = {k: env[k] for k in args.keys}

    try:
        output = export_env(env, scheme=args.scheme, mask=args.mask)
    except ExportError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(output)
    return 0
