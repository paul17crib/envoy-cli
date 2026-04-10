"""CLI commands: envoy lock / envoy unlock"""

import argparse
import getpass
import sys
from pathlib import Path

from envoy.locker import LockError, is_locked, lock_env, unlock_env
from envoy.sync import load_local


def build_parser(subparsers=None):
    desc = "Lock or unlock a .env file with a passphrase."
    if subparsers is not None:
        p = subparsers.add_parser("lock", help=desc)
    else:
        p = argparse.ArgumentParser(prog="envoy lock", description=desc)

    p.add_argument("file", help="Path to the .env file")
    p.add_argument(
        "--unlock", action="store_true", help="Unlock instead of locking"
    )
    p.add_argument(
        "--output", "-o", default=None,
        help="Write output to this path (default: overwrite input file)"
    )
    p.add_argument(
        "--passphrase", "-p", default=None,
        help="Passphrase (prompted if omitted)"
    )
    return p


def run_lock(args) -> int:
    src = Path(args.file)
    if not src.exists():
        print(f"[error] File not found: {src}", file=sys.stderr)
        return 1

    passphrase = args.passphrase or getpass.getpass("Passphrase: ")
    if not passphrase:
        print("[error] Passphrase must not be empty.", file=sys.stderr)
        return 1

    content = src.read_text()
    dest = Path(args.output) if args.output else src

    try:
        if args.unlock:
            if not is_locked(content):
                print(f"[error] File is not locked: {src}", file=sys.stderr)
                return 1
            env = unlock_env(content, passphrase)
            from envoy.parser import serialize_env
            dest.write_text(serialize_env(env))
            print(f"[ok] Unlocked → {dest}")
        else:
            if is_locked(content):
                print(f"[error] File is already locked: {src}", file=sys.stderr)
                return 1
            env = load_local(str(src))
            locked = lock_env(env, passphrase)
            dest.write_text(locked)
            print(f"[ok] Locked → {dest}")
    except LockError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    return 0
