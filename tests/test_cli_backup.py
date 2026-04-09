"""Tests for the backup CLI command."""

import argparse
from pathlib import Path
from datetime import datetime
import pytest
import time

from envoy.cli_backup import run_backup, cleanup_old_backups


@pytest.fixture
def tmp_env_file(tmp_path):
    """Create a temporary .env file for testing."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DATABASE_URL=postgres://localhost\n"
        "API_KEY=secret123\n"
        "DEBUG=true\n"
    )
    return env_file


@pytest.fixture
def backup_dir(tmp_path):
    """Create a backup directory."""
    return tmp_path / ".env.backups"


def make_args(file=".env", output_dir=".env.backups", mask=False, name=None, keep=None):
    """Helper to create argument namespace."""
    return argparse.Namespace(
        file=file,
        output_dir=output_dir,
        mask=mask,
        name=name,
        keep=keep
    )


def test_backup_creates_backup_file(tmp_env_file, backup_dir):
    """Test that backup creates a backup file."""
    args = make_args(
        file=str(tmp_env_file),
        output_dir=str(backup_dir)
    )
    
    result = run_backup(args)
    
    assert result == 0
    assert backup_dir.exists()
    backups = list(backup_dir.glob("*.env"))
    assert len(backups) == 1
    assert backups[0].read_text() == tmp_env_file.read_text()


def test_backup_missing_file_returns_error(tmp_path, backup_dir):
    """Test that backing up a missing file returns an error."""
    args = make_args(
        file=str(tmp_path / "missing.env"),
        output_dir=str(backup_dir)
    )
    
    result = run_backup(args)
    
    assert result == 1
    assert not backup_dir.exists()


def test_backup_with_custom_name(tmp_env_file, backup_dir):
    """Test backup with a custom name."""
    args = make_args(
        file=str(tmp_env_file),
        output_dir=str(backup_dir),
        name="custom_backup.env"
    )
    
    result = run_backup(args)
    
    assert result == 0
    backup_file = backup_dir / "custom_backup.env"
    assert backup_file.exists()


def test_backup_masks_sensitive_values(tmp_env_file, backup_dir):
    """Test that backup masks sensitive values when --mask is used."""
    args = make_args(
        file=str(tmp_env_file),
        output_dir=str(backup_dir),
        mask=True
    )
    
    result = run_backup(args)
    
    assert result == 0
    backups = list(backup_dir.glob("*.env"))
    backup_content = backups[0].read_text()
    
    assert "***" in backup_content
    assert "secret123" not in backup_content
    assert "DEBUG=true" in backup_content


def test_backup_keeps_only_recent_backups(tmp_env_file, backup_dir):
    """Test that --keep option removes old backups."""
    backup_dir.mkdir()
    
    # Create 5 backups with slight time differences
    for i in range(5):
        backup_file = backup_dir / f".env_{i:02d}.env"
        backup_file.write_text(f"VERSION={i}")
        time.sleep(0.01)  # Ensure different mtimes
    
    args = make_args(
        file=str(tmp_env_file),
        output_dir=str(backup_dir),
        keep=3
    )
    
    result = run_backup(args)
    
    assert result == 0
    backups = list(backup_dir.glob("*.env"))
    assert len(backups) == 3


def test_cleanup_old_backups(backup_dir):
    """Test cleanup_old_backups function directly."""
    backup_dir.mkdir()
    
    # Create test backup files
    for i in range(5):
        backup_file = backup_dir / f".env_{i:02d}.env"
        backup_file.write_text(f"VERSION={i}")
        time.sleep(0.01)
    
    cleanup_old_backups(backup_dir, ".env", 2)
    
    remaining = list(backup_dir.glob(".env_*.env"))
    assert len(remaining) == 2
