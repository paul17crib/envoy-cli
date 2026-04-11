"""CLI sub-commands for scope-based env filtering."""

import argparse
import sys
from typing import List, Optional

from envoy.scoper import extract_scope, inject_scope, list_scopes, remove_scope, ScopeError
from envoy.sync import load_local, save_local, SyncError
from envoy.parser import serialize_env


def build_parser(parent: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:
    desc = "Filter, prefix, or inspect env vars by scope."
    if parent is not None:
        parser = parent.add_parser("scope", help=desc, description=desc)
    else:
        parser = argparse.ArgumentParser(prog="envoy scope", description=desc)

    sub = parser.add_subparsers(dest="scope_cmd", required=True)

    # --- extract ---
    ex = sub.add_parser("extract", help="Keep only keys matching a scope prefix.")
    ex.add_argument("scope", help="Scope prefix, e.g. APP")
    ex.add_argument("--file", default=".env", help="Source .env file (default: .env)")
    ex.add_argument("--strip", action="store_true", help="Strip the prefix from output keys")
    ex.add_argument("--out", default=None, help="Write result to this file instead of stdout")

    # --- inject ---
    inj = sub.add_parser("inject", help="Add a scope prefix to all keys.")
    inj.add_argument("scope", help="Scope prefix to add, e.g. PROD")
    inj.add_argument("--file", default=".env", help="Source .env file (default: .env)")
    inj.add_argument("--out", default=None, help="Write result to this file instead of stdout")

    # --- list ---
    ls = sub.add_parser("list", help="List all scope prefixes found in the file.")
    ls.add_argument("--file", default=".env", help="Source .env file (default: .env)")

    # --- remove ---
    rm = sub.add_parser("remove", help="Remove all keys belonging to a scope.")
    rm.add_argument("scope", help="Scope prefix to remove, e.g. LEGACY")
    rm.add_argument("--file", default=".env", help="Source .env file (default: .env)")
    rm.add_argument("--out", default=None, help="Write result to this file; omit to overwrite source")

    return parser


def run_scope(args: argparse.Namespace) -> int:
    try:
        env = load_local(args.file)
    except SyncError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    cmd = args.scope_cmd

    if cmd == "list":
        scopes = list_scopes(env)
        if not scopes:
            print("(no scoped keys found)")
        else:
            for s in scopes:
                print(s)
        return 0

    if cmd == "extract":
        result = extract_scope(env, args.scope, strip_prefix=args.strip)
    elif cmd == "inject":
        result = inject_scope(env, args.scope)
    elif cmd == "remove":
        result = remove_scope(env, args.scope)
    else:
        print(f"[error] Unknown scope sub-command: {cmd}", file=sys.stderr)
        return 1

    serialized = serialize_env(result)

    out_path = getattr(args, "out", None)
    if cmd == "remove" and out_path is None:
        out_path = args.file

    if out_path:
        save_local(out_path, result, overwrite=True)
        print(f"Written to {out_path}")
    else:
        print(serialized, end="")

    return 0
