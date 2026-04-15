"""CLI command: envoy diff3 — compare multiple .env files side by side."""

from __future__ import annotations

import argparse
import sys
from typing import List

from envoy.parser import parse_env_file
from envoy.differ2 import multi_diff, MultiDiffReport
from envoy.masker import mask_env

_RESET = "\033[0m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_GREEN = "\033[32m"


def build_parser(parent: argparse._SubParsersAction = None) -> argparse.ArgumentParser:
    desc = "Compare multiple .env files side by side"
    if parent:
        p = parent.add_parser("diff3", help=desc)
    else:
        p = argparse.ArgumentParser(prog="envoy diff3", description=desc)
    p.add_argument("files", nargs="+", metavar="FILE", help="Two or more .env files")
    p.add_argument("--no-color", action="store_true", help="Disable ANSI colour output")
    p.add_argument("--no-mask", action="store_true", help="Do not mask sensitive values")
    p.add_argument("--conflicts-only", action="store_true", help="Show only conflicting keys")
    return p


def _color(text: str, code: str, use_color: bool) -> str:
    return f"{code}{text}{_RESET}" if use_color else text


def _print_report(report: MultiDiffReport, use_color: bool, mask: bool, conflicts_only: bool) -> None:
    col_w = 22
    header = "KEY".ljust(col_w) + "  ".join(f.ljust(col_w) for f in report.files)
    print(header)
    print("-" * len(header))

    for entry in report.entries:
        if conflicts_only and not entry.has_value_conflict:
            continue

        values = {
            fname: (mask_env({entry.key: v or ""})[entry.key] if mask and v else (v or ""))
            for fname, v in entry.values.items()
        }

        if entry.has_value_conflict:
            row_color = _RED
        elif entry.is_missing_in_some:
            row_color = _YELLOW
        else:
            row_color = _GREEN

        cells = "  ".join((values.get(f) or "<missing>").ljust(col_w) for f in report.files)
        line = entry.key.ljust(col_w) + cells
        print(_color(line, row_color, use_color))


def run_diff3(args: argparse.Namespace) -> int:
    if len(args.files) < 2:
        print("error: provide at least two files", file=sys.stderr)
        return 1

    envs = {}
    for path in args.files:
        try:
            envs[path] = parse_env_file(path)
        except FileNotFoundError:
            print(f"error: file not found: {path}", file=sys.stderr)
            return 1

    report = multi_diff(envs)
    use_color = not getattr(args, "no_color", False)
    mask = not getattr(args, "no_mask", False)
    conflicts_only = getattr(args, "conflicts_only", False)
    _print_report(report, use_color=use_color, mask=mask, conflicts_only=conflicts_only)
    return 0
