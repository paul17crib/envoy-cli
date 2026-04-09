"""Tests for the edit CLI command."""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from argparse import Namespace

from envoy.cli_edit import run_edit, get_editor, build_parser
from envoy.sync import save_local


@pytest.fixture
def tmp_env_file():
    """Create a temporary .env file for testing."""
    fd, path = tempfile.mkstemp(suffix='.env')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


def test_get_editor_from_arg():
    """Test that editor argument takes precedence."""
    assert get_editor('vim') == 'vim'


def test_get_editor_from_env():
    """Test that EDITOR environment variable is used."""
    with patch.dict(os.environ, {'EDITOR': 'emacs'}):
        assert get_editor(None) == 'emacs'


def test_get_editor_default():
    """Test that nano is the default editor."""
    with patch.dict(os.environ, {}, clear=True):
        assert get_editor(None) == 'nano'


def test_edit_creates_new_file(tmp_env_file):
    """Test editing creates a new file if it doesn't exist."""
    os.unlink(tmp_env_file)  # Remove the file
    
    args = Namespace(
        file=tmp_env_file,
        editor='cat',
        no_validate=True
    )
    
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        with patch('envoy.cli_edit.load_local') as mock_load:
            # First call raises FileNotFoundError, second returns edited content
            mock_load.side_effect = [FileNotFoundError(), {'NEW_KEY': 'new_value'}]
            
            result = run_edit(args)
            assert result == 0


def test_edit_saves_changes(tmp_env_file):
    """Test that editing saves changes to the file."""
    # Create initial file
    save_local(tmp_env_file, {'KEY1': 'value1'}, overwrite=True)
    
    args = Namespace(
        file=tmp_env_file,
        editor='cat',
        no_validate=True
    )
    
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        with patch('envoy.cli_edit.load_local') as mock_load:
            # First call returns original, second returns edited
            mock_load.side_effect = [
                {'KEY1': 'value1'},
                {'KEY1': 'value1', 'KEY2': 'value2'}
            ]
            
            result = run_edit(args)
            assert result == 0


def test_edit_validation_errors_prevent_save(tmp_env_file):
    """Test that validation errors prevent saving."""
    save_local(tmp_env_file, {'KEY1': 'value1'}, overwrite=True)
    
    args = Namespace(
        file=tmp_env_file,
        editor='cat',
        no_validate=False
    )
    
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        with patch('envoy.cli_edit.load_local') as mock_load:
            mock_load.side_effect = [
                {'KEY1': 'value1'},
                {'invalid-key': 'value'}  # Invalid key with hyphen
            ]
            
            result = run_edit(args)
            assert result == 1  # Should fail due to validation error


def test_edit_no_validate_skips_validation(tmp_env_file):
    """Test that --no-validate skips validation."""
    save_local(tmp_env_file, {'KEY1': 'value1'}, overwrite=True)
    
    args = Namespace(
        file=tmp_env_file,
        editor='cat',
        no_validate=True
    )
    
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        with patch('envoy.cli_edit.load_local') as mock_load:
            mock_load.side_effect = [
                {'KEY1': 'value1'},
                {'invalid-key': 'value'}  # Would normally fail validation
            ]
            
            result = run_edit(args)
            assert result == 0  # Should succeed despite invalid key
