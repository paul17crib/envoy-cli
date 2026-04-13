"""CLI command: envoy trace — show which env keys are used in source code."""

from __future__ import annotations

import argparse
from pathlib import Path

from envoy.sync import load_local, SyncError
from envoy.tracer import trace_env, unused_keys, undeclared_refs


def build_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        prog="envoy trace",
        description="Trace env key usage across source files.",
    )
    parser = parent.add_parser("trace", **kwargs) if parent else argparse.ArgumentParser(**kwargs)
    parser.add_argument("directory", help="Source directory to scan.")
    parser.add_argument("--env-file", default=".env", metavar="FILE", help="Env file to load (default: .env).")
    parser.add_argument("--ext", nargs="+", metavar="EXT", help="File extensions to scan (e.g. .py .js).")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--unused", action="store_true", help="Show only keys defined but never referenced.")
    mode.add_argument("--undeclared", action="store_true", help="Show only code references not in the env file.")
    return parser


def run_trace(args: argparse.Namespace) -> int:
    env_path = Path(args.env_file)
    try:
        env = load_local(env_path)
    except SyncError as exc:
        print(f"error: {exc}")
        return 1

    src_dir = Path(args.directory)
    if not src_dir.is_dir():
        print(f"error: directory not found: {src_dir}")
        return 1

    extensions = args.ext if args.ext else None

    if args.unused:
        keys = unused_keys(env, src_dir, extensions)
        if not keys:
            print("All keys are referenced in source code.")
        else:
            print(f"Unused keys ({len(keys)}):")
            for key in keys:
                print(f"  - {key}")
        return 0

    if args.undeclared:
        refs = undeclared_refs(env, src_dir, extensions)
        if not refs:
            print("No undeclared references found.")
        else:
            print(f"Undeclared references ({len(refs)}):")
            for key, files in sorted(refs.items()):
                print(f"  {key}")
                for f in files:
                    print(f"    {f}")
        return 0

    # Default: full usage report
    usage = trace_env(env, src_dir, extensions)
    print(f"{'KEY':<30}  {'REFERENCES'}")
    print("-" * 60)
    for key in sorted(usage):
        files = usage[key]
        if files:
            print(f"{key:<30}  {files[0]}")
            for f in files[1:]:
                print(f"{'':30}  {f}")
        else:
            print(f"{key:<30}  (not found)")
    return 0
