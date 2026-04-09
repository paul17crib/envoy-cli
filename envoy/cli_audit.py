import argparse
import sys
from envoy.sync import load_local, SyncError
from envoy.masker import get_masked_keys
from envoy.auditor import audit_env, format_audit_report


def build_parser(subparsers=None):
    description = "Audit a .env file for security and quality issues."
    if subparsers:
        parser = subparsers.add_parser("audit", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envoy audit", description=description)

    parser.add_argument(
        "file",
        nargs="?",
        default=".env",
        help="Path to the .env file (default: .env)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output audit results as JSON",
    )
    parser.add_argument(
        "--fail-on-warnings",
        action="store_true",
        help="Exit with non-zero status if any warnings are found",
    )
    return parser


def run_audit(args, out=sys.stdout, err=sys.stderr):
    try:
        env = load_local(args.file)
    except SyncError as e:
        err.write(f"Error: {e}\n")
        return 1

    results = audit_env(env)
    masked_keys = get_masked_keys(env)

    if getattr(args, "json", False):
        import json
        payload = [
            {
                "key": r.key,
                "level": r.level,
                "message": r.message,
            }
            for r in results
        ]
        out.write(json.dumps(payload, indent=2) + "\n")
    else:
        report = format_audit_report(results, masked_keys)
        out.write(report + "\n")

    has_errors = any(r.level == "error" for r in results)
    has_warnings = any(r.level == "warning" for r in results)

    if has_errors:
        return 1
    if getattr(args, "fail_on_warnings", False) and has_warnings:
        return 1
    return 0
