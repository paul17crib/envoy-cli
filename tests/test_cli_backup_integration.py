"""Integration tests for the backup CLI command."""

import argparse
from pathlib import Path
import pytest

from envoy.cli_backup import run_backup


@pytest.fixture
def complex_env_file(tmp_path):
    """Create a complex .env file for integration testing."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# Database configuration\n"
        "DATABASE_URL=postgres://user:pass@localhost:5432/db\n"
        "DB_PASSWORD=supersecret\n"
        "\n"
        "# API Settings\n"
        "API_KEY=sk_live_1234567890abcdef\n"
        "API_SECRET=secret_key_value\n"
        "API_ENDPOINT=https://api.example.com\n"
        "\n"
        "# Feature Flags\n"
        "ENABLE_FEATURE_X=true\n"
        "DEBUG=false\n"
    )
    return env_file


def make_args(file=".env", output_dir=".env.backups", mask=False, name=None, keep=None):
    """Helper to create argument namespace."""
    return argparse.Namespace(
        file=file,
        output_dir=output_dir,
        mask=mask,
        name=name,
        keep=keep
    )


def test_backup_preserves_comments_and_structure(complex_env_file, tmp_path):
    """Test that backup preserves comments and blank lines without masking."""
    backup_dir = tmp_path / "backups"
    args = make_args(
        file=str(complex_env_file),
        output_dir=str(backup_dir),
        mask=False
    )
    
    result = run_backup(args)
    
    assert result == 0
    backups = list(backup_dir.glob("*.env"))
    backup_content = backups[0].read_text()
    
    # Check original content is preserved
    assert "# Database configuration" in backup_content
    assert "DATABASE_URL=postgres://user:pass@localhost:5432/db" in backup_content
    assert "supersecret" in backup_content


def test_masked_backup_hides_all_secrets(complex_env_file, tmp_path):
    """Test that masked backup hides all sensitive values."""
    backup_dir = tmp_path / "backups"
    args = make_args(
        file=str(complex_env_file),
        output_dir=str(backup_dir),
        mask=True
    )
    
    result = run_backup(args)
    
    assert result == 0
    backups = list(backup_dir.glob("*.env"))
    backup_content = backups[0].read_text()
    
    # Check sensitive values are masked
    assert "supersecret" not in backup_content
    assert "sk_live_1234567890abcdef" not in backup_content
    assert "secret_key_value" not in backup_content
    
    # Check non-sensitive values are preserved
    assert "ENABLE_FEATURE_X=true" in backup_content
    assert "DEBUG=false" in backup_content
    assert "API_ENDPOINT=https://api.example.com" in backup_content


def test_multiple_backups_workflow(complex_env_file, tmp_path):
    """Test creating multiple backups and managing them."""
    backup_dir = tmp_path / "backups"
    
    # Create first backup
    args1 = make_args(
        file=str(complex_env_file),
        output_dir=str(backup_dir),
        name="backup_v1.env"
    )
    run_backup(args1)
    
    # Modify the file
    complex_env_file.write_text(
        complex_env_file.read_text() + "NEW_VAR=new_value\n"
    )
    
    # Create second backup
    args2 = make_args(
        file=str(complex_env_file),
        output_dir=str(backup_dir),
        name="backup_v2.env"
    )
    run_backup(args2)
    
    # Verify both backups exist and are different
    v1 = (backup_dir / "backup_v1.env").read_text()
    v2 = (backup_dir / "backup_v2.env").read_text()
    
    assert "NEW_VAR=new_value" not in v1
    assert "NEW_VAR=new_value" in v2
