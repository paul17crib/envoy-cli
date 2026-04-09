"""CLI command for interactively editing .env files with validation."""

import argparse
import os
import sys
import tempfile
import subprocess
from typing import Dict, Optional

from envoy.sync import load_local, save_local
from envoy.validator import validate_env, has_errors, format_issues
from envoy.parser import serialize_env


def build_parser(subparsers) -> argparse.ArgumentParser:
    """Build the 'edit' subcommand parser."""
    parser = subparsers.add_parser(
        'edit',
        help='Edit .env file with validation',
        description='Open .env file in editor with automatic validation after save'
    )
    parser.add_argument(
        '--file',
        default='.env',
        help='Path to .env file (default: .env)'
    )
    parser.add_argument(
        '--editor',
        default=None,
        help='Editor to use (default: $EDITOR or nano)'
    )
    parser.add_argument(
        '--no-validate',
        action='store_true',
        help='Skip validation after editing'
    )
    return parser


def get_editor(editor_arg: Optional[str]) -> str:
    """Get the editor to use for editing."""
    if editor_arg:
        return editor_arg
    return os.environ.get('EDITOR', 'nano')


def run_edit(args: argparse.Namespace) -> int:
    """Run the edit command."""
    env_file = args.file
    editor = get_editor(args.editor)
    
    # Load existing env or start with empty dict
    try:
        env_data = load_local(env_file)
    except FileNotFoundError:
        print(f"File {env_file} does not exist. Creating new file.")
        env_data = {}
    except Exception as e:
        print(f"Error loading {env_file}: {e}", file=sys.stderr)
        return 1
    
    # Create temporary file with current content
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as tmp:
        tmp.write(serialize_env(env_data))
        tmp_path = tmp.name
    
    try:
        # Open editor
        result = subprocess.run([editor, tmp_path])
        if result.returncode != 0:
            print(f"Editor exited with error code {result.returncode}", file=sys.stderr)
            return 1
        
        # Load edited content
        edited_env = load_local(tmp_path)
        
        # Validate if not disabled
        if not args.no_validate:
            issues = validate_env(edited_env)
            if issues:
                print("\nValidation issues found:")
                print(format_issues(issues))
                if has_errors(issues):
                    print("\nErrors found. File not saved.", file=sys.stderr)
                    return 1
        
        # Save to original file
        save_local(env_file, edited_env, overwrite=True)
        print(f"Successfully saved {env_file}")
        return 0
        
    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
