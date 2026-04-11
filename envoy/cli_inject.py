"""CLI command: envoy inject — run a command with env variables injected."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from envoy.injector import InjectionError, run_with_env
from envoy.sync import SyncError, load_local


def build_parser(parent: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:
    description = "Run a command with variables from an .env file injected."
    if parent is not None:
        parser = parent.add_parser("inject", help=description, description=description)
    else:
        parser = argparse.ArgumentParser(prog="envoy inject", description=description)

    parser.add_argument(
        "--file", "-f", default=".env", metavar="FILE",
        help="Path to the .env file (default: .env)",
    )
    parser.add_argument(
        "--no-inherit", action="store_true",
        help="Do not inherit the current process environment",
    )
    parser.add_argument(
        "--timeout", type=int, default=None, metavar="SECONDS",
        help="Timeout in seconds for the command",
    )
    parser.add_argument(
        "command", nargs=argparse.REMAINDER, metavar="COMMAND",
        help="Command and arguments to run",
    )
    return parser


def run_inject(args: argparse.Namespace) -> int:
    command: List[str] = args.command
    # Strip leading '--' separator if present
    if command and command[0] == "--":
        command = command[1:]

    if not command:
        print("error: no command specified", file=sys.stderr)
        return 1

    try:
        env = load_local(args.file)
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        result = run_with_env(
            command,
            env,
            inherit=not args.no_inherit,
            timeout=args.timeout,
        )
        return result.returncode
    except InjectionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError:
        print(f"error: command not found: {command[0]}", file=sys.stderr)
        return 127
