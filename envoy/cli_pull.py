"""CLI command for pulling .env files from a remote provider."""

import argparse
import sys
from pathlib import Path

from envoy.remote import FileRemoteProvider, pull
from envoy.sync import save_local, load_local, merge_envs, SyncError
from envoy.validator import validate_env, has_errors, format_issues
from envoy.display import format_env_table
from envoy.masker import mask_env


def run_pull(args: argparse.Namespace) -> int:
    """
    Pull remote .env contents and merge or overwrite the local file.

    Returns an exit code (0 = success, 1 = error).
    """
    remote_path = Path(args.remote)
    local_path = Path(args.local)

    provider = FileRemoteProvider(remote_path)

    try:
        remote_env = pull(provider)
    except Exception as exc:
        print(f"[error] Failed to pull from remote '{remote_path}': {exc}", file=sys.stderr)
        return 1

    if args.validate:
        issues = validate_env(remote_env)
        if has_errors(issues):
            print("[error] Remote env contains validation errors:", file=sys.stderr)
            for line in format_issues(issues):
                print(f"  {line}", file=sys.stderr)
            return 1

    if args.merge and local_path.exists():
        try:
            local_env = load_local(local_path)
        except SyncError as exc:
            print(f"[error] {exc}", file=sys.stderr)
            return 1
        merged = merge_envs(local_env, remote_env)
    else:
        merged = remote_env

    try:
        save_local(merged, local_path, overwrite=True)
    except SyncError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    display_env = mask_env(merged) if args.mask else merged

    print(f"[ok] Pulled {len(merged)} variable(s) from '{remote_path}' → '{local_path}'")

    if args.show:
        print()
        print(format_env_table(display_env))

    return 0


def build_parser(subparsers=None):
    description = "Pull a .env file from a remote source."
    if subparsers is not None:
        parser = subparsers.add_parser("pull", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envoy pull", description=description)

    parser.add_argument("remote", help="Path to the remote .env file")
    parser.add_argument(
        "--local", default=".env", help="Path to the local .env file (default: .env)"
    )
    parser.add_argument(
        "--merge", action="store_true", help="Merge remote values into existing local file"
    )
    parser.add_argument(
        "--validate", action="store_true", help="Validate remote env before writing"
    )
    parser.add_argument(
        "--show", action="store_true", help="Display the resulting env table after pull"
    )
    parser.add_argument(
        "--mask", action="store_true", help="Mask sensitive values in the display output"
    )
    return parser
