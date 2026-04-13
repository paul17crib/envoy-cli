"""CLI command: envoy label — add, remove, and list labels on .env keys."""

from __future__ import annotations

import argparse
import sys
from typing import List

from envoy.labeler import (
    LabelError,
    extract_labels,
    filter_by_label,
    list_all_labels,
    remove_labels,
    set_labels,
)
from envoy.sync import load_local, save_local, SyncError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy label",
        description="Add, remove, or list labels on .env keys.",
    )
    parser.add_argument("--file", default=".env", help="Path to .env file.")
    sub = parser.add_subparsers(dest="action", required=True)

    add_p = sub.add_parser("add", help="Add labels to a key.")
    add_p.add_argument("key", help="Key to label.")
    add_p.add_argument("labels", nargs="+", help="Labels to add.")
    add_p.add_argument("--dry-run", action="store_true")

    rm_p = sub.add_parser("remove", help="Remove all labels from a key.")
    rm_p.add_argument("key", help="Key to unlabel.")
    rm_p.add_argument("--dry-run", action="store_true")

    sub.add_parser("list", help="List all labels in the file.")

    filter_p = sub.add_parser("filter", help="Show keys matching a label.")
    filter_p.add_argument("label", help="Label to filter by.")

    return parser


def run_label(args: argparse.Namespace) -> int:
    try:
        env = load_local(args.file)
    except SyncError as exc:
        if args.action in ("list",):
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        env = {}

    if args.action == "add":
        try:
            existing = extract_labels(env).get(args.key, [])
            merged = sorted(set(existing) | set(args.labels))
            updated = set_labels(env, args.key, merged)
        except LabelError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        if args.dry_run:
            print(f"[dry-run] Would set labels on '{args.key}': {merged}")
        else:
            save_local(args.file, updated)
            print(f"Labels set on '{args.key}': {merged}")
        return 0

    if args.action == "remove":
        updated = remove_labels(env, args.key)
        if args.dry_run:
            print(f"[dry-run] Would remove labels from '{args.key}'.")
        else:
            save_local(args.file, updated)
            print(f"Labels removed from '{args.key}'.")
        return 0

    if args.action == "list":
        labels = list_all_labels(env)
        if not labels:
            print("No labels found.")
        else:
            for lbl in labels:
                print(lbl)
        return 0

    if args.action == "filter":
        matched = filter_by_label(env, args.label)
        if not matched:
            print(f"No keys found with label '{args.label}'.")
        else:
            for key, value in matched.items():
                print(f"{key}={value}")
        return 0

    return 1
