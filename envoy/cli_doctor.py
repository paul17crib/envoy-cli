"""cli_doctor.py — 'envoy doctor' command for environment health diagnostics.

Runs a series of checks on a .env file and reports issues with keys,
values, formatting, secrets hygiene, and overall structure.
"""

import argparse
import sys
from pathlib import Path

from envoy.parser import parse_env_file
from envoy.validator import validate_env, has_errors, format_issues
from envoy.auditor import audit_env, format_audit_report
from envoy.masker import get_masked_keys
from envoy.sync import SyncError


def build_parser(subparsers=None):
    """Build argument parser for the 'doctor' subcommand."""
    description = "Run health diagnostics on a .env file."
    if subparsers is not None:
        parser = subparsers.add_parser("doctor", help=description, description=description)
    else:
        parser = argparse.ArgumentParser(prog="envoy doctor", description=description)

    parser.add_argument(
        "file",
        nargs="?",
        default=".env",
        help="Path to the .env file to diagnose (default: .env)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors (non-zero exit on any issue)",
    )
    parser.add_argument(
        "--skip-audit",
        action="store_true",
        help="Skip secret hygiene audit checks",
    )
    parser.add_argument(
        "--skip-validate",
        action="store_true",
        help="Skip key/value validation checks",
    )
    return parser


def run_doctor(args, out=None, err=None):
    """Execute the doctor command.

    Args:
        args: Parsed argument namespace.
        out: Output stream (defaults to sys.stdout).
        err: Error stream (defaults to sys.stderr).

    Returns:
        int: Exit code (0 = healthy, 1 = issues found).
    """
    if out is None:
        out = sys.stdout
    if err is None:
        err = sys.stderr

    env_path = Path(args.file)

    # --- File existence check ---
    if not env_path.exists():
        print(f"[error] File not found: {env_path}", file=err)
        return 1

    try:
        env = parse_env_file(str(env_path))
    except SyncError as exc:
        print(f"[error] Failed to parse {env_path}: {exc}", file=err)
        return 1

    print(f"envoy doctor — diagnosing: {env_path}", file=out)
    print(f"  {len(env)} key(s) found", file=out)

    found_issues = False

    # --- Validation pass ---
    if not args.skip_validate:
        issues = validate_env(env)
        if issues:
            found_issues = True
            print("\n[validation]", file=out)
            for line in format_issues(issues):
                print(f"  {line}", file=out)
        else:
            print("\n[validation] OK — no key/value issues found.", file=out)

        if has_errors(issues):
            # Hard errors always fail regardless of --strict
            return 1

    # --- Audit pass ---
    if not args.skip_audit:
        audit_results = audit_env(env)
        if audit_results:
            found_issues = True
            print("\n[audit]", file=out)
            for line in format_audit_report(audit_results):
                print(f"  {line}", file=out)
        else:
            print("\n[audit] OK — no secret hygiene issues found.", file=out)

    # --- Summary ---
    masked_keys = get_masked_keys(env)
    print(f"\n[summary]", file=out)
    print(f"  Total keys   : {len(env)}", file=out)
    print(f"  Sensitive keys: {len(masked_keys)}", file=out)

    if found_issues:
        if args.strict:
            print("\n[result] FAIL — issues detected (strict mode).", file=out)
            return 1
        print("\n[result] WARN — minor issues detected.", file=out)
        return 0

    print("\n[result] PASS — environment looks healthy.", file=out)
    return 0
