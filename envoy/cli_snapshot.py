"""CLI commands for snapshot management: save, load, list, delete."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from envoy.snapshotter import save_snapshot, load_snapshot, list_snapshots, delete_snapshot
from envoy.sync import load_local, save_local, SyncError


def build_parser(subparsers=None):
    if subparsers is None:
        parser = argparse.ArgumentParser(description="Manage .env snapshots")
    else:
        parser = subparsers.add_parser("snapshot", help="Manage .env snapshots")

    sub = parser.add_subparsers(dest="snapshot_cmd")

    save_p = sub.add_parser("save", help="Save current .env as a named snapshot")
    save_p.add_argument("name", help="Snapshot name")
    save_p.add_argument("--file", default=".env", help="Source .env file")
    save_p.add_argument("--note", default="", help="Optional description")

    load_p = sub.add_parser("restore", help="Restore a snapshot to a .env file")
    load_p.add_argument("name", help="Snapshot name")
    load_p.add_argument("--file", default=".env", help="Target .env file")
    load_p.add_argument("--overwrite", action="store_true")

    sub.add_parser("list", help="List all saved snapshots")

    del_p = sub.add_parser("delete", help="Delete a named snapshot")
    del_p.add_argument("name", help="Snapshot name")

    return parser


def run_snapshot(args, out=None, err=None) -> int:
    out = out or sys.stdout
    err = err or sys.stderr

    cmd = getattr(args, "snapshot_cmd", None)

    if cmd == "save":
        try:
            env = load_local(args.file)
        except SyncError as e:
            err.write(f"Error: {e}\n")
            return 1
        path = save_snapshot(args.name, env, note=args.note)
        out.write(f"Snapshot '{args.name}' saved to {path}\n")
        return 0

    elif cmd == "restore":
        try:
            env = load_snapshot(args.name)
        except FileNotFoundError as e:
            err.write(f"Error: {e}\n")
            return 1
        try:
            save_local(args.file, env, overwrite=args.overwrite)
        except SyncError as e:
            err.write(f"Error: {e}\n")
            return 1
        out.write(f"Restored snapshot '{args.name}' to {args.file}\n")
        return 0

    elif cmd == "list":
        snapshots = list_snapshots()
        if not snapshots:
            out.write("No snapshots found.\n")
            return 0
        out.write(f"{'NAME':<20} {'KEYS':>5}  {'CREATED':<28}  NOTE\n")
        out.write("-" * 70 + "\n")
        for s in snapshots:
            out.write(f"{s['name']:<20} {s['key_count']:>5}  {s['created_at']:<28}  {s['note']}\n")
        return 0

    elif cmd == "delete":
        if delete_snapshot(args.name):
            out.write(f"Snapshot '{args.name}' deleted.\n")
            return 0
        err.write(f"Error: Snapshot '{args.name}' not found.\n")
        return 1

    else:
        err.write("No snapshot subcommand given. Use save, restore, list, or delete.\n")
        return 1
