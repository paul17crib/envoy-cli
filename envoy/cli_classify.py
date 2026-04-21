"""CLI command: envoy classify — show env keys grouped by semantic category."""

from __future__ import annotations

import argparse
import sys
from typing import List

from envoy.classifier import classify_env, group_by_category, list_categories
from envoy.masker import mask_env
from envoy.sync import SyncError, load_local


def build_parser(sub: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    kwargs = dict(
        description="Classify env keys into semantic categories.",
    )
    if sub is not None:
        parser = sub.add_parser("classify", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="envoy classify", **kwargs)

    parser.add_argument("file", nargs="?", default=".env", help="Path to .env file")
    parser.add_argument(
        "--category",
        metavar="CAT",
        help="Show only keys in this category",
    )
    parser.add_argument(
        "--no-mask",
        action="store_true",
        help="Reveal sensitive values (masked by default)",
    )
    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="Print available category names and exit",
    )
    return parser


def run_classify(args: argparse.Namespace) -> int:
    if args.list_categories:
        for cat in sorted(list_categories()):
            print(cat)
        return 0

    try:
        env = load_local(args.file)
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    display_env = env if args.no_mask else mask_env(env)
    classified = classify_env(display_env)
    groups = group_by_category(classified)

    filter_cat = args.category

    printed_any = False
    for category in sorted(groups):
        if filter_cat and category != filter_cat:
            continue
        items = groups[category]
        print(f"[{category}]")
        for ck in sorted(items, key=lambda x: x.key):
            marker = "*" if ck.sensitive else " "
            print(f"  {marker} {ck.key}={ck.value}")
        printed_any = True

    if filter_cat and not printed_any:
        print(f"no keys found in category '{filter_cat}'", file=sys.stderr)
        return 1

    return 0
