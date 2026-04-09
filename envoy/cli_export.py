"""Export command - exports environment variables in various formats."""

import argparse
import json
import sys
from typing import Dict

from envoy.parser import parse_env_file
from envoy.masker import mask_env


def build_parser(subparsers) -> argparse.ArgumentParser:
    """Build the export command parser."""
    parser = subparsers.add_parser(
        'export',
        help='Export environment variables in various formats'
    )
    parser.add_argument(
        'file',
        nargs='?',
        default='.env',
        help='Path to .env file (default: .env)'
    )
    parser.add_argument(
        '--format',
        choices=['bash', 'json', 'docker', 'yaml'],
        default='bash',
        help='Export format (default: bash)'
    )
    parser.add_argument(
        '--no-mask',
        action='store_true',
        help='Do not mask sensitive values'
    )
    parser.add_argument(
        '--prefix',
        default='',
        help='Add prefix to all variable names'
    )
    return parser


def format_bash(env_vars: Dict[str, str], prefix: str = '') -> str:
    """Format as bash export statements."""
    lines = []
    for key, value in sorted(env_vars.items()):
        prefixed_key = f"{prefix}{key}"
        # Escape single quotes in value
        escaped_value = value.replace("'", "'\\''")
        lines.append(f"export {prefixed_key}='{escaped_value}'")
    return '\n'.join(lines)


def format_docker(env_vars: Dict[str, str], prefix: str = '') -> str:
    """Format as Docker ENV statements."""
    lines = []
    for key, value in sorted(env_vars.items()):
        prefixed_key = f"{prefix}{key}"
        # Escape quotes and backslashes
        escaped_value = value.replace('\\', '\\\\').replace('"', '\\"')
        lines.append(f'ENV {prefixed_key}="{escaped_value}"')
    return '\n'.join(lines)


def format_yaml(env_vars: Dict[str, str], prefix: str = '') -> str:
    """Format as YAML."""
    lines = []
    for key, value in sorted(env_vars.items()):
        prefixed_key = f"{prefix}{key}"
        # Simple YAML string escaping
        if '"' in value or '\n' in value or value.startswith(' '):
            escaped_value = value.replace('\\', '\\\\').replace('"', '\\"')
            lines.append(f'{prefixed_key}: "{escaped_value}"')
        else:
            lines.append(f'{prefixed_key}: {value}')
    return '\n'.join(lines)


def run_export(args: argparse.Namespace) -> int:
    """Execute the export command."""
    try:
        env_vars = parse_env_file(args.file)
    except FileNotFoundError:
        print(f"Error: File '{args.file}' not found", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error parsing file: {e}", file=sys.stderr)
        return 1

    if not args.no_mask:
        env_vars = mask_env(env_vars)

    if args.format == 'bash':
        output = format_bash(env_vars, args.prefix)
    elif args.format == 'json':
        prefixed = {f"{args.prefix}{k}": v for k, v in env_vars.items()}
        output = json.dumps(prefixed, indent=2)
    elif args.format == 'docker':
        output = format_docker(env_vars, args.prefix)
    elif args.format == 'yaml':
        output = format_yaml(env_vars, args.prefix)
    else:
        print(f"Error: Unknown format '{args.format}'", file=sys.stderr)
        return 1

    print(output)
    return 0
