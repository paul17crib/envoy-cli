"""CLI command: envoy compose — apply a pipeline of transforms to a .env file."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from envoy.composer import ComposerError, compose, list_steps, preview_compose
from envoy.parser import parse_env_file, serialize_env
from envoy.sync import SyncError, load_local, save_local


def build_parser(parent: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:
    description = "Apply a named pipeline of transforms to a .env file."
    if parent is not None:
        p = parent.add_parser("compose", help=description, description=description)
    else:
        p = argparse.ArgumentParser(prog="envoy compose", description=description)

    p.add_argument("file", help="Path to the .env file")
    p.add_argument(
        "steps",
        nargs="+",
        metavar="STEP",
        help=f"One or more transform steps to apply in order. Available: {', '.join(list_steps())}",
    )
    p.add_argument("--dry-run", action="store_true", help="Print result to stdout without writing")
    p.add_argument("--preview", action="store_true", help="Show env state after each step")
    p.add_argument("--output", metavar="FILE", help="Write result to a different file")
    return p


def run_compose(args: argparse.Namespace) -> int:
    try:
        env = load_local(args.file)
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        if args.preview:
            snapshots = preview_compose(env, args.steps)
            for snap in snapshots:
                print(f"[{snap['step']}] {snap['keys']} keys")
                for k, v in snap["env"].items():  # type: ignore[union-attr]
                    print(f"  {k}={v}")
            return 0

        result = compose(env, args.steps)
    except ComposerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    output = serialize_env(result)

    if args.dry_run:
        print(output)
        return 0

    dest = args.output if args.output else args.file
    try:
        save_local(dest, result, overwrite=True)
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    applied = ", ".join(args.steps)
    print(f"Applied [{applied}] → {dest} ({len(result)} keys)")
    return 0
