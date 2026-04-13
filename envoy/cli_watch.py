"""CLI command: envoy watch — monitor a .env file for live changes."""

from __future__ import annotations

import argparse
import sys
from typing import List

from envoy.watcher import watch, watch_once, WatchEvent
from envoy.masker import mask_env


def build_parser(sub=None) -> argparse.ArgumentParser:
    kwargs = dict(
        description="Watch a .env file for changes and display diffs."
    )
    if sub is not None:
        parser = sub.add_parser("watch", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)
    parser.add_argument("file", help="Path to the .env file to watch")
    parser.add_argument(
        "--interval", type=float, default=1.0,
        help="Polling interval in seconds (default: 1.0)"
    )
    parser.add_argument(
        "--no-mask", action="store_true",
        help="Show sensitive values unmasked"
    )
    parser.add_argument(
        "--once", action="store_true",
        help="Check once and exit (useful for testing)"
    )
    return parser


def _format_event(event: WatchEvent, mask: bool) -> List[str]:
    lines = [f"[watch] Changes detected in {event.path}:"]
    display = mask_env(event.current) if mask else event.current
    for entry in event.changes:
        val = display.get(entry.key, entry.new_value or "")
        if entry.symbol == "+":
            lines.append(f"  + {entry.key}={val}")
        elif entry.symbol == "-":
            lines.append(f"  - {entry.key}")
        elif entry.symbol == "~":
            lines.append(f"  ~ {entry.key}={val}")
    return lines


def run_watch(args: argparse.Namespace) -> int:
    mask = not getattr(args, "no_mask", False)

    if getattr(args, "once", False):
        from envoy.parser import parse_env_file
        try:
            previous = parse_env_file(args.file)
        except FileNotFoundError:
            print(f"[watch] File not found: {args.file}", file=sys.stderr)
            return 1
        event = watch_once(args.file, previous)
        for line in _format_event(event, mask):
            print(line)
        return 0

    print(f"[watch] Watching {args.file} (interval={args.interval}s) ...")

    def on_change(event: WatchEvent) -> None:
        for line in _format_event(event, mask):
            print(line)

    try:
        watch(args.file, on_change, interval=args.interval)
    except KeyboardInterrupt:
        print("\n[watch] Stopped.")
    return 0


if __name__ == "__main__":
    sys.exit(run_watch(build_parser().parse_args()))
