"""CLI command for merging multiple .env files."""

import argparse
import sys
from typing import Dict, List

from envoy.parser import parse_env_file, serialize_env
from envoy.sync import merge_envs, save_local
from envoy.masker import mask_env
from envoy.display import format_env_table


def build_parser(subparsers) -> argparse.ArgumentParser:
    """Build the merge subcommand parser."""
    parser = subparsers.add_parser(
        'merge',
        help='Merge multiple .env files into one',
        description='Merge multiple .env files with priority given to later files'
    )
    parser.add_argument(
        'files',
        nargs='+',
        help='Env files to merge (later files override earlier ones)'
    )
    parser.add_argument(
        '-o', '--output',
        default='.env',
        help='Output file path (default: .env)'
    )
    parser.add_argument(
        '--no-overwrite',
        action='store_true',
        help='Do not overwrite output file if it exists'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show the result without writing to file'
    )
    parser.add_argument(
        '--no-mask',
        action='store_true',
        help='Show actual values in dry-run (default: masked)'
    )
    parser.set_defaults(func=run_merge)
    return parser


def run_merge(args: argparse.Namespace) -> int:
    """Execute the merge command."""
    merged: Dict[str, str] = {}
    
    # Merge files in order
    for filepath in args.files:
        try:
            env_data = parse_env_file(filepath)
            merged = merge_envs(merged, env_data)
        except FileNotFoundError:
            print(f"Error: File not found: {filepath}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error reading {filepath}: {e}", file=sys.stderr)
            return 1
    
    if not merged:
        print("Warning: No environment variables found in any file", file=sys.stderr)
        return 0
    
    # Dry run - just display
    if args.dry_run:
        display_data = merged if args.no_mask else mask_env(merged)
        print(f"\nMerged result ({len(merged)} variables):\n")
        print(format_env_table(display_data))
        print(f"\nWould write to: {args.output}")
        return 0
    
    # Write to output file
    try:
        save_local(args.output, merged, overwrite=not args.no_overwrite)
        print(f"Successfully merged {len(args.files)} files into {args.output}")
        print(f"Total variables: {len(merged)}")
        return 0
    except FileExistsError:
        print(f"Error: {args.output} already exists. Use --no-overwrite=false or choose different output.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error writing to {args.output}: {e}", file=sys.stderr)
        return 1
