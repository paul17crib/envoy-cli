"""CLI command: envoy duplicate — copy env keys under new names."""

from __future__ import annotations

import argparse
import sys
from typing import List

from envoy.duplicator import DuplicatorError, duplicate_keys, preview_duplications
from envoy.sync import SyncError, load_local, save_local


def build_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[name-defined]
    description = "Duplicate one or more keys within an .env file."
    if parent is not None:
        parser = parent.add_parser("duplicate", help=description, description=description)
    else:
        parser = argparse.ArgumentParser(prog="envoy duplicate", description=description)

    parser.add_argument("file", help="Path to the .env file.")
    parser.add_argument(
        "pairs",
        nargs="+",
        metavar="SOURCE:DEST",
        help="Key pairs to duplicate, e.g. DB_URL:DATABASE_URL.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite destination key if it already exists.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Preview changes without writing to disk.",
    )
    return parser


def _parse_pairs(raw: List[str]) -> dict:
    mapping: dict = {}
    for item in raw:
        if ":" not in item:
            print(f"[error] Invalid pair '{item}' — expected SOURCE:DEST format.", file=sys.stderr)
            sys.exit(1)
        src, _, dst = item.partition(":")
        mapping[src.strip()] = dst.strip()
    return mapping


def run_duplicate(args: argparse.Namespace) -> int:
    try:
        env = load_local(args.file)
    except SyncError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    mapping = _parse_pairs(args.pairs)

    if args.dry_run:
        preview = preview_duplications(env, mapping)
        for entry in preview:
            conflict_note = " [CONFLICT — will be skipped without --overwrite]" if entry["conflict"] else ""
            print(f"  {entry['source']} -> {entry['dest']}{conflict_note}")
        return 0

    try:
        updated = duplicate_keys(env, mapping, overwrite=args.overwrite)
    except DuplicatorError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    try:
        save_local(args.file, updated, overwrite=True)
    except SyncError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    added = [dst for src, dst in mapping.items() if dst not in env]
    replaced = [dst for src, dst in mapping.items() if dst in env and args.overwrite]
    print(f"Duplicated {len(mapping)} key(s): {len(added)} added, {len(replaced)} replaced.")
    return 0
