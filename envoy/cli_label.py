"""CLI command for managing labels on .env file entries."""

import argparse
import sys

from envoy.parser import parse_env_file, serialize_env
from envoy.labeler import extract_labels, set_labels, remove_labels, list_labeled_keys


def build_parser(subparsers=None):
    """Build the argument parser for the label command."""
    description = "Add, remove, or list labels on .env file keys."
    if subparsers is not None:
        parser = subparsers.add_parser("label", help=description, description=description)
    else:
        parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "file",
        nargs="?",
        default=".env",
        help="Path to the .env file (default: .env)",
    )

    sub = parser.add_subparsers(dest="label_cmd")

    # label set KEY label1 label2 ...
    set_p = sub.add_parser("set", help="Set labels on a key")
    set_p.add_argument("key", help="Key to label")
    set_p.add_argument("labels", nargs="+", help="Labels to assign")
    set_p.add_argument("--append", action="store_true", help="Append to existing labels instead of replacing")
    set_p.add_argument("--dry-run", action="store_true", help="Preview changes without writing")

    # label remove KEY label1 label2 ...
    rm_p = sub.add_parser("remove", help="Remove labels from a key")
    rm_p.add_argument("key", help="Key to modify")
    rm_p.add_argument("labels", nargs="+", help="Labels to remove")
    rm_p.add_argument("--dry-run", action="store_true", help="Preview changes without writing")

    # label list
    list_p = sub.add_parser("list", help="List all labeled keys")
    list_p.add_argument("--filter", dest="label_filter", metavar="LABEL", help="Only show keys with this label")

    # label show KEY
    show_p = sub.add_parser("show", help="Show labels for a specific key")
    show_p.add_argument("key", help="Key to inspect")

    return parser


def run_label(args):
    """Execute the label subcommand."""
    if not hasattr(args, "label_cmd") or args.label_cmd is None:
        print("Usage: envoy label <set|remove|list|show> [options]", file=sys.stderr)
        return 1

    try:
        env = parse_env_file(args.file)
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        return 1

    if args.label_cmd == "set":
        if args.key not in env:
            print(f"Error: key '{args.key}' not found in {args.file}", file=sys.stderr)
            return 1
        existing = extract_labels(env).get(args.key, set()) if args.append else set()
        new_labels = existing | set(args.labels)
        updated = set_labels(env, args.key, sorted(new_labels))
        if args.dry_run:
            print(f"[dry-run] Would set labels on '{args.key}': {', '.join(sorted(new_labels))}")
            return 0
        with open(args.file, "w") as f:
            f.write(serialize_env(updated))
        print(f"Labels set on '{args.key}': {', '.join(sorted(new_labels))}")
        return 0

    elif args.label_cmd == "remove":
        if args.key not in env:
            print(f"Error: key '{args.key}' not found in {args.file}", file=sys.stderr)
            return 1
        current = extract_labels(env).get(args.key, set())
        remaining = current - set(args.labels)
        if remaining:
            updated = set_labels(env, args.key, sorted(remaining))
        else:
            updated = remove_labels(env, args.key)
        if args.dry_run:
            removed = current & set(args.labels)
            print(f"[dry-run] Would remove labels from '{args.key}': {', '.join(sorted(removed))}")
            return 0
        with open(args.file, "w") as f:
            f.write(serialize_env(updated))
        print(f"Labels updated on '{args.key}'.")
        return 0

    elif args.label_cmd == "list":
        labeled = list_labeled_keys(env)
        if not labeled:
            print("No labeled keys found.")
            return 0
        for key, labels in sorted(labeled.items()):
            if args.label_filter and args.label_filter not in labels:
                continue
            print(f"{key}: {', '.join(sorted(labels))}")
        return 0

    elif args.label_cmd == "show":
        all_labels = extract_labels(env)
        labels = all_labels.get(args.key, set())
        if not labels:
            print(f"No labels found for '{args.key}'.")
        else:
            print(f"{args.key}: {', '.join(sorted(labels))}")
        return 0

    print(f"Unknown label subcommand: {args.label_cmd}", file=sys.stderr)
    return 1
