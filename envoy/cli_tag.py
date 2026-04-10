"""CLI subcommand: envoy tag — manage tags on .env keys."""

import argparse
import sys
from typing import List, Optional

from envoy.sync import load_local, save_local, SyncError
from envoy.tagger import set_tags, remove_tags, filter_by_tag, list_tags, extract_tags


def build_parser(subparsers=None):
    desc = "Manage tags on .env keys"
    if subparsers is not None:
        p = subparsers.add_parser("tag", help=desc)
    else:
        p = argparse.ArgumentParser(prog="envoy tag", description=desc)

    p.add_argument("--file", "-f", default=".env", help="Path to .env file")
    sub = p.add_subparsers(dest="tag_cmd")

    # set
    ps = sub.add_parser("set", help="Set tags on a key")
    ps.add_argument("key", help="Key to tag")
    ps.add_argument("tags", nargs="+", help="Tags to assign")

    # remove
    pr = sub.add_parser("remove", help="Remove all tags from a key")
    pr.add_argument("key", help="Key to untag")

    # list
    sub.add_parser("list", help="List all tags in use")

    # filter
    pf = sub.add_parser("filter", help="Show keys matching a tag")
    pf.add_argument("tag", help="Tag to filter by")

    # show
    psh = sub.add_parser("show", help="Show tags for a specific key")
    psh.add_argument("key", help="Key to inspect")

    return p


def run_tag(args) -> int:
    if not args.tag_cmd:
        print("Usage: envoy tag <set|remove|list|filter|show>", file=sys.stderr)
        return 1

    try:
        env = load_local(args.file)
    except SyncError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.tag_cmd == "set":
        updated = set_tags(env, args.key, args.tags)
        save_local(args.file, updated, overwrite=True)
        print(f"Tagged '{args.key}' with: {', '.join(sorted(args.tags))}")
        return 0

    if args.tag_cmd == "remove":
        updated = remove_tags(env, args.key)
        save_local(args.file, updated, overwrite=True)
        print(f"Removed all tags from '{args.key}'")
        return 0

    if args.tag_cmd == "list":
        tags = list_tags(env)
        if not tags:
            print("No tags found.")
        else:
            for t in tags:
                print(t)
        return 0

    if args.tag_cmd == "filter":
        matched = filter_by_tag(env, args.tag)
        if not matched:
            print(f"No keys tagged with '{args.tag}'.")
        else:
            for k, v in matched.items():
                print(f"{k}={v}")
        return 0

    if args.tag_cmd == "show":
        tags_map = extract_tags(env)
        key_tags = tags_map.get(args.key, [])
        if not key_tags:
            print(f"'{args.key}' has no tags.")
        else:
            print(f"{args.key}: {', '.join(key_tags)}")
        return 0

    print(f"Unknown tag subcommand: {args.tag_cmd}", file=sys.stderr)
    return 1
