"""CLI commands for pinning and drift-checking env keys."""

from __future__ import annotations

import argparse
import sys
from typing import List

from envoy.masker import mask_env
from envoy.pinner import (
    PinError,
    check_drift,
    load_pins,
    pin_keys,
    save_pins,
    unpin_keys,
)
from envoy.sync import SyncError, load_local


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy pin", description="Pin env keys and detect drift."
    )
    sub = parser.add_subparsers(dest="action", required=True)

    add_p = sub.add_parser("add", help="Pin one or more keys.")
    add_p.add_argument("keys", nargs="+")
    add_p.add_argument("--file", default=".env")
    add_p.add_argument("--pin-file", default=".env.pins")

    rm_p = sub.add_parser("remove", help="Unpin one or more keys.")
    rm_p.add_argument("keys", nargs="+")
    rm_p.add_argument("--pin-file", default=".env.pins")

    check_p = sub.add_parser("check", help="Check for drift against pinned values.")
    check_p.add_argument("--file", default=".env")
    check_p.add_argument("--pin-file", default=".env.pins")
    check_p.add_argument("--no-mask", action="store_true")

    sub.add_parser("list", help="List all pinned keys.").add_argument(
        "--pin-file", default=".env.pins"
    )

    return parser


def run_pin(args: argparse.Namespace) -> int:
    try:
        if args.action == "add":
            env = load_local(args.file)
            pins = load_pins(args.pin_file)
            pins = pin_keys(env, args.keys, existing_pins=pins)
            save_pins(pins, args.pin_file)
            print(f"Pinned {len(args.keys)} key(s) to '{args.pin_file}'.")

        elif args.action == "remove":
            pins = load_pins(args.pin_file)
            pins = unpin_keys(args.keys, pins)
            save_pins(pins, args.pin_file)
            print(f"Unpinned {len(args.keys)} key(s).")

        elif args.action == "check":
            env = load_local(args.file)
            pins = load_pins(args.pin_file)
            if not pins:
                print("No pins defined.")
                return 0
            drift = check_drift(env, pins)
            display = env if getattr(args, "no_mask", False) else mask_env(env)
            if not drift:
                print(f"No drift detected. {len(pins)} key(s) match pinned values.")
                return 0
            print(f"Drift detected in {len(drift)} key(s):")
            for key, info in drift.items():
                status = info["status"]
                current = display.get(key, "<missing>")
                print(f"  [{status}] {key}: pinned={info['pinned']!r}  current={current!r}")
            return 1

        elif args.action == "list":
            pins = load_pins(args.pin_file)
            if not pins:
                print("No keys are pinned.")
                return 0
            for key, val in sorted(pins.items()):
                print(f"  {key}={val!r}")

    except (PinError, SyncError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0
