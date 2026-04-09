import argparse
from envoy.sync import load_local, SyncError
from envoy.masker import is_sensitive_key
from envoy.auditor import audit_env


def build_parser(subparsers=None):
    description = "Show statistics and summary about a .env file."
    if subparsers:
        parser = subparsers.add_parser("stats", help=description)
    else:
        parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "file",
        nargs="?",
        default=".env",
        help="Path to the .env file (default: .env)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Output stats as JSON",
    )
    return parser


def collect_stats(env: dict) -> dict:
    total = len(env)
    sensitive = [k for k in env if is_sensitive_key(k)]
    empty = [k for k in env if env[k] == ""]
    audit_results = audit_env(env)
    errors = [r for r in audit_results if r.level == "error"]
    warnings = [r for r in audit_results if r.level == "warning"]
    return {
        "total_keys": total,
        "sensitive_keys": len(sensitive),
        "empty_values": len(empty),
        "audit_errors": len(errors),
        "audit_warnings": len(warnings),
        "sensitive_key_names": sensitive,
        "empty_key_names": empty,
    }


def run_stats(args) -> int:
    try:
        env = load_local(args.file)
    except SyncError as e:
        print(f"Error: {e}")
        return 1

    stats = collect_stats(env)

    if args.as_json:
        import json
        print(json.dumps(stats, indent=2))
        return 0

    print(f"File         : {args.file}")
    print(f"Total keys   : {stats['total_keys']}")
    print(f"Sensitive keys: {stats['sensitive_keys']}")
    print(f"Empty values : {stats['empty_values']}")
    print(f"Audit errors : {stats['audit_errors']}")
    print(f"Audit warnings: {stats['audit_warnings']}")

    if stats["sensitive_key_names"]:
        print("Sensitive    : " + ", ".join(stats["sensitive_key_names"]))
    if stats["empty_key_names"]:
        print("Empty keys   : " + ", ".join(stats["empty_key_names"]))

    return 0
