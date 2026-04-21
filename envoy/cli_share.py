"""envoy share — CLI for creating and managing shareable env snapshots."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envoy.parser import parse_env_file
from envoy.sharer import ShareError, create_share, list_shares, load_share, revoke_share


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="envoy share", description="Share env snapshots")
    sub = p.add_subparsers(dest="action", required=True)

    cr = sub.add_parser("create", help="Create a shareable snapshot")
    cr.add_argument("file", help="Source .env file")
    cr.add_argument("--label", required=True, help="Human-readable label")
    cr.add_argument("--ttl", type=int, default=3600, help="TTL in seconds (default 3600)")
    cr.add_argument("--no-mask", action="store_true", help="Do not mask sensitive values")
    cr.add_argument("--share-dir", default=".", help="Directory for share storage")

    ls = sub.add_parser("list", help="List all shares")
    ls.add_argument("--share-dir", default=".", help="Directory for share storage")

    gt = sub.add_parser("get", help="Retrieve a share by token")
    gt.add_argument("token", help="Share token")
    gt.add_argument("--share-dir", default=".", help="Directory for share storage")

    rv = sub.add_parser("revoke", help="Revoke a share by token")
    rv.add_argument("token", help="Share token")
    rv.add_argument("--share-dir", default=".", help="Directory for share storage")

    return p


def run_share(args: argparse.Namespace) -> int:
    base = Path(args.share_dir)

    if args.action == "create":
        src = Path(args.file)
        if not src.exists():
            print(f"error: file not found: {src}", file=sys.stderr)
            return 1
        try:
            env = parse_env_file(src)
            token = create_share(
                env,
                label=args.label,
                ttl_seconds=args.ttl,
                mask=not args.no_mask,
                base=base,
            )
            print(f"Share created. Token: {token}")
            return 0
        except ShareError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1

    if args.action == "list":
        shares = list_shares(base=base)
        if not shares:
            print("No shares found.")
            return 0
        for s in shares:
            status = "EXPIRED" if s["expired"] else "active"
            print(f"{s['token']}  {s['label']:<24}  {status}")
        return 0

    if args.action == "get":
        try:
            env = load_share(args.token, base=base)
            for k, v in env.items():
                print(f"{k}={v}")
            return 0
        except ShareError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1

    if args.action == "revoke":
        removed = revoke_share(args.token, base=base)
        if removed:
            print(f"Revoked share: {args.token}")
            return 0
        print(f"error: share not found: {args.token}", file=sys.stderr)
        return 1

    return 0
