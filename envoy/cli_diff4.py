"""CLI command: envoy diff4 — three-way diff of .env files."""
from __future__ import annotations

import argparse
import sys
from typing import List

from envoy.differ3 import ThreeWayEntry, ThreeWayReport, three_way_diff
from envoy.sync import load_local, SyncError

_ANSI = {
    "!": "\033[91m",  # red — conflict
    "-": "\033[93m",  # yellow — only in ours
    "+": "\033[92m",  # green — only in theirs
    "~": "\033[94m",  # blue — changed
    "=": "",           # unchanged
}
_RESET = "\033[0m"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envoy diff4",
        description="Three-way diff between a base, ours, and theirs .env file.",
    )
    p.add_argument("base", help="Base .env file (common ancestor)")
    p.add_argument("ours", help="Our .env file")
    p.add_argument("theirs", help="Their .env file")
    p.add_argument("--no-color", action="store_true", help="Disable ANSI colours")
    p.add_argument("--conflicts-only", action="store_true", help="Show only conflicting keys")
    return p


def _colorize(symbol: str, text: str, no_color: bool) -> str:
    if no_color or symbol not in _ANSI or not _ANSI[symbol]:
        return text
    return f"{_ANSI[symbol]}{text}{_RESET}"


def _print_report(report: ThreeWayReport, no_color: bool, conflicts_only: bool) -> None:
    for entry in report.entries:
        if conflicts_only and not entry.has_conflict:
            continue
        sym = entry.symbol
        base_val = entry.base if entry.base is not None else "<absent>"
        ours_val = entry.ours if entry.ours is not None else "<absent>"
        theirs_val = entry.theirs if entry.theirs is not None else "<absent>"
        line = f"{sym} {entry.key}  base={base_val!r}  ours={ours_val!r}  theirs={theirs_val!r}"
        print(_colorize(sym, line, no_color))


def run_diff4(args: argparse.Namespace) -> int:
    try:
        base_env = load_local(args.base)
        ours_env = load_local(args.ours)
        theirs_env = load_local(args.theirs)
    except SyncError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    report = three_way_diff(base_env, ours_env, theirs_env)
    _print_report(report, no_color=args.no_color, conflicts_only=args.conflicts_only)

    if report.has_conflicts:
        print(
            f"\n{len(report.conflicts)} conflict(s) detected.",
            file=sys.stderr,
        )
        return 2
    return 0
