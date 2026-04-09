"""CLI command for removing environment variables from .env files."""

import argparse
import sys
from pathlib import Path

from envoy.parser import parse_env_file, serialize_env


def build_parser(subparsers) -> argparse.ArgumentParser:
    """Build the 'unset' subcommand parser."""
    parser = subparsers.add_parser(
        'unset',
        help='Remove environment variables from .env file',
        description='Remove one or more environment variables from a .env file'
    )
    parser.add_argument(
        'keys',
        nargs='+',
        help='Environment variable key(s) to remove'
    )
    parser.add_argument(
        '-f', '--file',
        default='.env',
        help='Path to .env file (default: .env)'
    )
    parser.add_argument(
        '--ignore-missing',
        action='store_true',
        help='Do not error if key does not exist'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be removed without actually removing'
    )
    parser.set_defaults(func=run_unset)
    return parser


def run_unset(args) -> int:
    """Execute the unset command."""
    env_file = Path(args.file)
    
    # Check if file exists
    if not env_file.exists():
        print(f"Error: File '{env_file}' not found.", file=sys.stderr)
        return 1
    
    # Load existing env
    env_vars = parse_env_file(env_file)
    
    # Track what was removed and what was missing
    removed = []
    missing = []
    
    for key in args.keys:
        if key in env_vars:
            removed.append(key)
            if not args.dry_run:
                del env_vars[key]
        else:
            missing.append(key)
    
    # Handle missing keys
    if missing and not args.ignore_missing:
        print(f"Error: Keys not found in {env_file}:", file=sys.stderr)
        for key in missing:
            print(f"  - {key}", file=sys.stderr)
        return 1
    
    # Check if anything was removed
    if not removed:
        if args.ignore_missing:
            print(f"No keys removed from {env_file}")
            return 0
        else:
            print(f"Error: No matching keys found in {env_file}", file=sys.stderr)
            return 1
    
    # Write back to file (unless dry run)
    if not args.dry_run:
        content = serialize_env(env_vars)
        env_file.write_text(content)
    
    # Display confirmation
    action = "Would remove" if args.dry_run else "Removed"
    for key in removed:
        print(f"{action} {key} from {env_file}")
    
    if missing and args.ignore_missing:
        print(f"\nSkipped (not found): {', '.join(missing)}")
    
    return 0
