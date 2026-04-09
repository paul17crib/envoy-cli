"""Tests for the set CLI command."""

import pytest
from pathlib import Path
from argparse import Namespace

from envoy.cli_set import run_set
from envoy.parser import parse_env_file


@pytest.fixture
def tmp_env_file(tmp_path):
    """Create a temporary .env file."""
    env_file = tmp_path / ".env"
    env_file.write_text("EXISTING_KEY=old_value\nANOTHER_KEY=another_value\n")
    return env_file


def make_args(**kwargs):
    """Helper to create args namespace."""
    defaults = {
        'key': 'TEST_KEY',
        'value': 'test_value',
        'file': '.env',
        'create': False,
        'validate': True
    }
    defaults.update(kwargs)
    return Namespace(**defaults)


def test_set_adds_new_key_to_existing_file(tmp_env_file, capsys):
    """Test adding a new key to an existing file."""
    args = make_args(file=str(tmp_env_file), key='NEW_KEY', value='new_value')
    result = run_set(args)
    
    assert result == 0
    env_vars = parse_env_file(tmp_env_file)
    assert env_vars['NEW_KEY'] == 'new_value'
    assert env_vars['EXISTING_KEY'] == 'old_value'
    
    captured = capsys.readouterr()
    assert 'Added NEW_KEY=new_value' in captured.out


def test_set_updates_existing_key(tmp_env_file, capsys):
    """Test updating an existing key."""
    args = make_args(file=str(tmp_env_file), key='EXISTING_KEY', value='updated_value')
    result = run_set(args)
    
    assert result == 0
    env_vars = parse_env_file(tmp_env_file)
    assert env_vars['EXISTING_KEY'] == 'updated_value'
    
    captured = capsys.readouterr()
    assert 'Updated EXISTING_KEY=updated_value' in captured.out


def test_set_creates_new_file_with_create_flag(tmp_path, capsys):
    """Test creating a new file with --create flag."""
    new_file = tmp_path / "new.env"
    args = make_args(file=str(new_file), key='FIRST_KEY', value='first_value', create=True)
    result = run_set(args)
    
    assert result == 0
    assert new_file.exists()
    env_vars = parse_env_file(new_file)
    assert env_vars['FIRST_KEY'] == 'first_value'
    
    captured = capsys.readouterr()
    assert 'Added FIRST_KEY=first_value' in captured.out


def test_set_fails_without_create_flag(tmp_path, capsys):
    """Test that set fails on missing file without --create."""
    missing_file = tmp_path / "missing.env"
    args = make_args(file=str(missing_file), key='KEY', value='value')
    result = run_set(args)
    
    assert result == 1
    assert not missing_file.exists()
    
    captured = capsys.readouterr()
    assert 'not found' in captured.err
    assert '--create' in captured.err


def test_set_masks_sensitive_values_in_output(tmp_env_file, capsys):
    """Test that sensitive values are masked in output."""
    args = make_args(file=str(tmp_env_file), key='API_SECRET', value='secret123')
    result = run_set(args)
    
    assert result == 0
    env_vars = parse_env_file(tmp_env_file)
    assert env_vars['API_SECRET'] == 'secret123'  # Stored unmasked
    
    captured = capsys.readouterr()
    assert '***MASKED***' in captured.out
    assert 'secret123' not in captured.out


def test_set_validates_key_by_default(tmp_env_file, capsys):
    """Test that invalid keys are rejected by default."""
    args = make_args(file=str(tmp_env_file), key='invalid-key', value='value')
    result = run_set(args)
    
    assert result == 1
    
    captured = capsys.readouterr()
    assert 'Invalid key name' in captured.err


def test_set_allows_invalid_key_with_no_validate(tmp_env_file):
    """Test that validation can be disabled."""
    args = make_args(file=str(tmp_env_file), key='invalid-key', value='value', validate=False)
    result = run_set(args)
    
    assert result == 0
    env_vars = parse_env_file(tmp_env_file)
    assert env_vars['invalid-key'] == 'value'


def test_set_handles_values_with_spaces(tmp_env_file):
    """Test setting values with spaces."""
    args = make_args(file=str(tmp_env_file), key='MESSAGE', value='hello world')
    result = run_set(args)
    
    assert result == 0
    env_vars = parse_env_file(tmp_env_file)
    assert env_vars['MESSAGE'] == 'hello world'


def test_set_handles_empty_value(tmp_env_file):
    """Test setting an empty value."""
    args = make_args(file=str(tmp_env_file), key='EMPTY_KEY', value='')
    result = run_set(args)
    
    assert result == 0
    env_vars = parse_env_file(tmp_env_file)
    assert env_vars['EMPTY_KEY'] == ''
