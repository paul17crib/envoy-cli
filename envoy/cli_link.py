"""cli_link.py — CLI command: envoy link"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envoy.linker import LinkerError, apply_links, get_linked_keys, parse_link_file
from envoy.sync import SyncError, load_local, save_local


def build_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        prog="envoy link",
        description="Copy env values to new keys using a link-map file.",
    )
    parser = parent.add_parser("link", **kwargs) if parent else argparse.ArgumentParser(**kwargs)
    parser.add_argument("env_file", help="Target .env file")
    parser.add_argument("link_file", help="Link-map file (SRC -> DST per line)")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing destination keys",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print what would change without writing",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        default=False,
        help="Print result to stdout instead of writing the file",
    )
    return parser


def run_link(args: argparse.Namespace) -> int:
    # Load env
    try:
        env = load_local(args.env_file)
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    # Load link map
    link_path = Path(args.link_file)
    if not link_path.exists():
        print(f"error: link file not found: {args.link_file}", file=sys.stderr)
        return 1

    try:
        link_map = parse_link_file(link_path.read_text())
    except LinkerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not link_map:
        print("warning: link file contains no mappings", file=sys.stderr)
        return 0

    # Apply
    try:
        linked = apply_links(env, link_map, overwrite=args.overwrite)
    except LinkerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    new_keys = get_linked_keys(env, link_map)

    if args.dry_run:
        for key in new_keys:
            dst = link_map.get(key, key)
            print(f"  {key} -> {dst} = {linked.get(dst, '')}")
        print(f"dry-run: {len(new_keys)} key(s) would be linked")
        return 0

    if args.stdout:
        for k, v in linked.items():
            print(f"{k}={v}")
        return 0

    try:
        save_local(args.env_file, linked, overwrite=True)
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"linked {len(new_keys)} key(s) in {args.env_file}")
    return 0
