"""CLI subcommand: envoy comparator — compare two .env files and report similarity."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from envoy.comparator import compare_envs, format_comparison_report
from envoy.sync import load_local, SyncError


def build_parser(parent: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:
    description = "Compare two .env files and report key overlap and value similarity."
    if parent is not None:
        parser = parent.add_parser("comparator", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envoy comparator", description=description)

    parser.add_argument("left", help="First .env file (left side)")
    parser.add_argument("right", help="Second .env file (right side)")
    parser.add_argument(
        "--show-matching",
        action="store_true",
        default=False,
        help="Print keys with identical values in both files.",
    )
    parser.add_argument(
        "--show-differing",
        action="store_true",
        default=False,
        help="Print keys whose values differ between files.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output report as JSON.",
    )
    return parser


def run_comparator(args: argparse.Namespace) -> int:
    try:
        left_env = load_local(args.left)
    except SyncError as exc:
        print(f"Error loading {args.left}: {exc}", file=sys.stderr)
        return 1

    try:
        right_env = load_local(args.right)
    except SyncError as exc:
        print(f"Error loading {args.right}: {exc}", file=sys.stderr)
        return 1

    report = compare_envs(left_env, right_env)

    if args.json:
        import json
        data = {
            "similarity_score": report.similarity_score,
            "total_unique_keys": report.total_unique_keys,
            "shared_keys": report.shared_keys,
            "only_in_left": report.only_in_left,
            "only_in_right": report.only_in_right,
            "matching_keys": report.matching_keys,
            "differing_keys": report.differing_keys,
        }
        print(json.dumps(data, indent=2))
        return 0

    left_label = args.left
    right_label = args.right
    print(format_comparison_report(report, left_label=left_label, right_label=right_label))

    if args.show_matching and report.matching_keys:
        print("\nMatching keys:")
        for k in report.matching_keys:
            print(f"  = {k}")

    if args.show_differing and report.differing_keys:
        print("\nDiffering keys:")
        for k in report.differing_keys:
            print(f"  ~ {k}  ({left_label}: {left_env[k]!r}  |  {right_label}: {right_env[k]!r})")

    return 0
