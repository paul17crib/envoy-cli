import argparse
import sys
from envoy.sync import load_local, SyncError
from envoy.masker import mask_env
from envoy.display import format_env_table


def build_parser(subparsers=None):
    description = "Search for keys or values in a .env file"
    if subparsers:
        parser = subparsers.add_parser("search", help=description)
    else:
        parser = argparse.ArgumentParser(description=description)

    parser.add_argument("query", help="Search term to match against keys or values")
    parser.add_argument(
        "--file", "-f", default=".env", help="Path to the .env file (default: .env)"
    )
    parser.add_argument(
        "--keys-only", action="store_true", help="Search only in key names"
    )
    parser.add_argument(
        "--values-only", action="store_true", help="Search only in values"
    )
    parser.add_argument(
        "--no-mask", action="store_true", help="Show sensitive values unmasked"
    )
    parser.add_argument(
        "--case-sensitive", action="store_true", help="Use case-sensitive matching"
    )
    return parser


def run_search(args, out=None):
    if out is None:
        out = sys.stdout

    try:
        env = load_local(args.file)
    except SyncError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    query = args.query if args.case_sensitive else args.query.lower()

    results = {}
    for key, value in env.items():
        k = key if args.case_sensitive else key.lower()
        v = value if args.case_sensitive else value.lower()

        if args.keys_only:
            match = query in k
        elif args.values_only:
            match = query in v
        else:
            match = query in k or query in v

        if match:
            results[key] = value

    if not results:
        print(f"No matches found for '{args.query}'.", file=out)
        return 0

    display = mask_env(results) if not args.no_mask else results
    print(f"Found {len(results)} match(es) for '{args.query}':", file=out)
    print(format_env_table(display), file=out)
    return 0
