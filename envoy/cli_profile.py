"""CLI sub-command: envoy profile — list, switch, and inspect env profiles."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from envoy.profiler import (
    DEFAULT_PROFILE,
    active_profile,
    list_profiles,
    load_profile,
    save_profile,
    set_active_profile,
)
from envoy.sync import SyncError
from envoy.display import format_env_table
from envoy.masker import mask_env


def build_parser(subparsers=None) -> argparse.ArgumentParser:
    desc = "Manage named .env profiles"
    if subparsers is not None:
        parser = subparsers.add_parser("profile", help=desc)
    else:
        parser = argparse.ArgumentParser(prog="envoy profile", description=desc)

    parser.add_argument("--file", default=".env", help="Base env file (default: .env)")
    sub = parser.add_subparsers(dest="profile_cmd")

    sub.add_parser("list", help="List available profiles")

    use_p = sub.add_parser("use", help="Switch the active profile")
    use_p.add_argument("name", help="Profile name to activate")

    show_p = sub.add_parser("show", help="Display contents of a profile")
    show_p.add_argument("name", nargs="?", default=None, help="Profile name (default: active)")
    show_p.add_argument("--no-mask", action="store_true", help="Reveal sensitive values")

    cp_p = sub.add_parser("copy", help="Copy one profile to another")
    cp_p.add_argument("src", help="Source profile name")
    cp_p.add_argument("dest", help="Destination profile name")
    cp_p.add_argument("--overwrite", action="store_true", help="Overwrite destination if it exists")

    return parser


def run_profile(args: argparse.Namespace) -> int:
    base = args.file
    cmd = args.profile_cmd

    if cmd == "list" or cmd is None:
        profiles = list_profiles(base)
        active = active_profile(base)
        if not profiles:
            print("No profiles found.")
            return 0
        for name in profiles:
            marker = " *" if name == active else ""
            print(f"  {name}{marker}")
        return 0

    if cmd == "use":
        try:
            load_profile(base, args.name)  # validate existence
        except SyncError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        set_active_profile(base, args.name)
        print(f"Active profile set to '{args.name}'.")
        return 0

    if cmd == "show":
        name = args.name or active_profile(base) or DEFAULT_PROFILE
        try:
            env = load_profile(base, name)
        except SyncError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        display = env if args.no_mask else mask_env(env)
        print(format_env_table(display, title=f"Profile: {name}"))
        return 0

    if cmd == "copy":
        try:
            env = load_profile(base, args.src)
            path = save_profile(base, args.dest, env, overwrite=args.overwrite)
        except SyncError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        print(f"Copied profile '{args.src}' → '{path}'.")
        return 0

    print(f"Unknown profile sub-command: {cmd}", file=sys.stderr)
    return 1
