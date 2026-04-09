"""CLI command for backing up .env files."""

import argparse
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from envoy.parser import parse_env_file, serialize_env
from envoy.masker import mask_env


def build_parser(subparsers) -> argparse.ArgumentParser:
    """Build the backup subcommand parser."""
    parser = subparsers.add_parser(
        'backup',
        help='Create a backup of an .env file',
        description='Create a timestamped backup of an .env file with optional masking'
    )
    parser.add_argument(
        'file',
        nargs='?',
        default='.env',
        help='Path to the .env file to backup (default: .env)'
    )
    parser.add_argument(
        '-o', '--output-dir',
        default='.env.backups',
        help='Directory to store backups (default: .env.backups)'
    )
    parser.add_argument(
        '--mask',
        action='store_true',
        help='Mask sensitive values in the backup'
    )
    parser.add_argument(
        '--name',
        help='Custom backup name (default: timestamped)'
    )
    parser.add_argument(
        '--keep',
        type=int,
        help='Keep only the N most recent backups, delete older ones'
    )
    parser.set_defaults(func=run_backup)
    return parser


def run_backup(args: argparse.Namespace) -> int:
    """Execute the backup command."""
    env_file = Path(args.file)
    
    if not env_file.exists():
        print(f"Error: File '{env_file}' does not exist")
        return 1
    
    # Create backup directory
    backup_dir = Path(args.output_dir)
    backup_dir.mkdir(exist_ok=True)
    
    # Generate backup filename
    if args.name:
        backup_name = args.name
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{env_file.stem}_{timestamp}{env_file.suffix}"
    
    backup_path = backup_dir / backup_name
    
    # Create backup
    if args.mask:
        env_data = parse_env_file(str(env_file))
        masked_data = mask_env(env_data)
        serialized = serialize_env(masked_data)
        backup_path.write_text(serialized)
        print(f"Created masked backup: {backup_path}")
    else:
        shutil.copy2(env_file, backup_path)
        print(f"Created backup: {backup_path}")
    
    # Clean up old backups if requested
    if args.keep is not None:
        cleanup_old_backups(backup_dir, env_file.stem, args.keep)
    
    return 0


def cleanup_old_backups(backup_dir: Path, prefix: str, keep: int) -> None:
    """Remove old backups, keeping only the N most recent."""
    pattern = f"{prefix}_*"
    backups = sorted(
        backup_dir.glob(pattern),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    for old_backup in backups[keep:]:
        old_backup.unlink()
        print(f"Removed old backup: {old_backup}")
