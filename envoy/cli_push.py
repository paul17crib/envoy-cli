import argparse
import sys
from envoy.sync import load_local, SyncError
from envoy.remote import FileRemoteProvider, RemoteProvider
from envoy.masker import mask_env, get_masked_keys
from envoy.display import format_env_table
from envoy.validator import validate_env, has_errors, format_issues


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy push",
        description="Push local .env file to a remote provider.",
    )
    parser.add_argument(
        "--file", "-f", default=".env", help="Local .env file to push (default: .env)"
    )
    parser.add_argument(
        "--remote", "-r", required=True, help="Remote path or URL to push to"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview what would be pushed without writing"
    )
    parser.add_argument(
        "--skip-validation", action="store_true", help="Skip validation before pushing"
    )
    parser.add_argument(
        "--show-values", action="store_true", help="Show unmasked values in preview"
    )
    return parser


def run_push(args: argparse.Namespace, provider: RemoteProvider = None) -> int:
    try:
        local_env = load_local(args.file)
    except SyncError as e:
        print(f"[error] {e}", file=sys.stderr)
        return 1

    if not args.skip_validation:
        issues = validate_env(local_env)
        if has_errors(issues):
            print("[error] Validation failed. Fix the following issues before pushing:\n")
            print(format_issues(issues))
            return 1
        if issues:
            print("[warn] Validation warnings:\n")
            print(format_issues(issues))

    if args.dry_run:
        display = local_env if args.show_values else mask_env(local_env)
        masked_keys = get_masked_keys(local_env)
        print(f"[dry-run] Would push {len(local_env)} key(s) to '{args.remote}'")
        if masked_keys:
            print(f"[dry-run] Masked keys: {', '.join(sorted(masked_keys))}")
        print()
        print(format_env_table(display))
        return 0

    if provider is None:
        provider = FileRemoteProvider(args.remote)

    try:
        provider.push(local_env)
        print(f"[ok] Pushed {len(local_env)} key(s) to '{args.remote}'")
        return 0
    except Exception as e:
        print(f"[error] Push failed: {e}", file=sys.stderr)
        return 1
