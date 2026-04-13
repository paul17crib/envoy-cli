"""cli_plan.py — CLI interface for the env migration planner."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from envoy.planner import MigrationPlan, apply_plan, build_plan
from envoy.sync import SyncError, load_local, save_local


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envoy plan",
        description="Show or apply a migration plan between two .env files.",
    )
    p.add_argument("source", help="Source .env file (current state)")
    p.add_argument("target", help="Target .env file (desired state)")
    p.add_argument(
        "--apply",
        metavar="OUTPUT",
        help="Apply the plan and write result to OUTPUT (use '-' for stdout)",
    )
    p.add_argument(
        "--rename",
        metavar="OLD:NEW",
        action="append",
        default=[],
        help="Treat OLD key as renamed to NEW (repeatable)",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colour output",
    )
    return p


def _color(text: str, code: str, enabled: bool) -> str:
    return f"\033[{code}m{text}\033[0m" if enabled else text


def _print_plan(plan: MigrationPlan, color: bool) -> None:
    if plan.is_empty:
        print("No changes.")
        return
    action_colors = {
        "add": "32",
        "remove": "31",
        "update": "33",
        "rename": "36",
    }
    for step in plan.steps:
        code = action_colors.get(step.action, "0")
        print(_color(repr(step), code, color))


def run_plan(args: argparse.Namespace) -> int:
    try:
        source_env = load_local(args.source)
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        target_env = load_local(args.target)
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    renames: dict[str, str] = {}
    for pair in args.rename:
        if ":" not in pair:
            print(f"error: --rename value must be OLD:NEW, got {pair!r}", file=sys.stderr)
            return 1
        old, new = pair.split(":", 1)
        renames[old.strip()] = new.strip()

    plan = build_plan(source_env, target_env, renames=renames)
    color = not args.no_color

    _print_plan(plan, color)

    if args.apply:
        result = apply_plan(source_env, plan)
        if args.apply == "-":
            from envoy.parser import serialize_env
            print(serialize_env(result), end="")
        else:
            try:
                save_local(args.apply, result, overwrite=True)
                print(f"Written to {args.apply}")
            except SyncError as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 1

    return 0
