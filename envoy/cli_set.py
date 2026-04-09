"""CLI command for setting environment variables in .env files."""

import argparse
import sys
from pathlib import Path
from typing import Dict

from envoy.parser import parse_env_file, serialize_env
from envoy.validator import validate_key
from envoy.masker import is_sensitive_key


def build_parser(subparsers) -> argparse.ArgumentParser:
    """Build the 'set' subcommand parser."""
    parser = subparsers.add_parser(
        'set',
        help='Set or update environment variables in .env file',
        description='Set or update one or more environment variables in a .env file'
    )
    parser.add_argument(
        'key',
        help='Environment variable key to set'
    )
    parser.add_argument(
        'value',
        help='Value to set for the key'
    )
    parser.add_argument(
        '-f', '--file',
        default='.env',
        help='Path to .env file (default: .env)'
    )
    parser.add_argument(
        '--create',
        action='store_true',
        help='Create the file if it does not exist'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        default=True,
        help='Validate key name (default: enabled)'
    )
    parser.add_argument(
        '--no-validate',
        dest='validate',
        action='store_false',
        help='Skip key validation'
    )
    parser.set_defaults(func=run_set)
    return parser


def run_set(args) -> int:
    """Execute the set command."""
    env_file = Path(args.file)
    
    # Validate key if requested
    if args.validate:
        issues = validate_key(args.key)
        errors = [i for i in issues if i.level == 'error']
        if errors:
            print(f"Error: Invalid key name '{args.key}':", file=sys.stderr)
            for issue in errors:
                print(f"  - {issue.message}", file=sys.stderr)
            return 1
    
    # Load existing env or create new dict
    if env_file.exists():
        env_vars = parse_env_file(env_file)
    elif args.create:
        env_vars = {}
    else:
        print(f"Error: File '{env_file}' not found. Use --create to create it.", file=sys.stderr)
        return 1
    
    # Check if key is being updated or added
    is_update = args.key in env_vars
    
    # Set the value
    env_vars[args.key] = args.value
    
    # Write back to file
    try:
        content = serialize_env(env_vars)
        env_file.write_text(content)
    except OSError as e:
        print(f"Error: Could not write to '{env_file}': {e}", file=sys.stderr)
        return 1
    
    # Display confirmation
    action = "Updated" if is_update else "Added"
    display_value = args.value
    if is_sensitive_key(args.key):
        display_value = "***MASKED***"
    
    print(f"{action} {args.key}={display_value} in {env_file}")
    return 0
