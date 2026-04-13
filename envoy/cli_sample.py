"""CLI command: envoy sample — randomly sample keys from a .env file."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from envoy.masker import mask_env
from envoy.sampler import SamplerError, sample_fraction, sample_keys
from envoy.sync import SyncError, load_local
from envoy.parser import serialize_env


def build_parser(subparsers=None) -> argparse.ArgumentParser:
    desc = "Randomly sample a subset of keys from a .env file."
    if subparsers is not None:
        parser = subparsers.add_parser("sample", help=desc, description=desc)
    else:
        parser = argparse.ArgumentParser(prog="envoy sample", description=desc)
    parser.add_argument("file", help="Path to the .env file.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-n", "--count", type=int, metavar="N",
                       help="Number of keys to sample.")
    group.add_argument("-f", "--fraction", type=float, metavar="F",
                       help="Fraction of keys to sample (0.0–1.0).")
    parser.add_argument("--keys", nargs="+", metavar="KEY",
                        help="Restrict sampling pool to these keys.")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for reproducibility.")
    parser.add_argument("--no-mask", action="store_true",
                        help="Reveal sensitive values (masked by default).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print sampled keys without writing anything.")
    parser.add_argument("-o", "--output", metavar="FILE",
                        help="Write sampled env to this file instead of stdout.")
    return parser


def run_sample(args: argparse.Namespace) -> int:
    try:
        env = load_local(args.file)
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        if args.count is not None:
            result = sample_keys(env, args.count, seed=args.seed, keys=args.keys)
        else:
            if args.keys:
                print("error: --keys cannot be combined with --fraction",
                      file=sys.stderr)
                return 1
            result = sample_fraction(env, args.fraction, seed=args.seed)
    except SamplerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    display = result if args.no_mask else mask_env(result)
    lines = [f"{k}={v}" for k, v in display.items()]
    output = "\n".join(lines) + ("\n" if lines else "")

    if not args.dry_run and args.output:
        try:
            with open(args.output, "w") as fh:
                fh.write(serialize_env(result))
            print(f"Wrote {len(result)} key(s) to {args.output}")
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
    else:
        print(output, end="")

    return 0
