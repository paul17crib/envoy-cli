"""Tests for the merge CLI command."""

import os
import tempfile
import pytest
from argparse import Namespace
from pathlib import Path

from envoy.cli_merge import run_merge
from envoy.parser import parse_env_file


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_merge_combines_multiple_files(temp_dir, capsys):
    """Test merging multiple env files."""
    file1 = os.path.join(temp_dir, 'file1.env')
    file2 = os.path.join(temp_dir, 'file2.env')
    output = os.path.join(temp_dir, 'merged.env')
    
    Path(file1).write_text('KEY1=value1\nKEY2=value2\n')
    Path(file2).write_text('KEY3=value3\n')
    
    args = Namespace(
        files=[file1, file2],
        output=output,
        no_overwrite=False,
        dry_run=False,
        no_mask=False
    )
    
    result = run_merge(args)
    assert result == 0
    
    merged = parse_env_file(output)
    assert merged == {'KEY1': 'value1', 'KEY2': 'value2', 'KEY3': 'value3'}
    
    captured = capsys.readouterr()
    assert 'Successfully merged' in captured.out
    assert 'Total variables: 3' in captured.out


def test_merge_later_files_override_earlier(temp_dir):
    """Test that later files override earlier ones."""
    file1 = os.path.join(temp_dir, 'file1.env')
    file2 = os.path.join(temp_dir, 'file2.env')
    output = os.path.join(temp_dir, 'merged.env')
    
    Path(file1).write_text('KEY1=original\nKEY2=value2\n')
    Path(file2).write_text('KEY1=overridden\n')
    
    args = Namespace(
        files=[file1, file2],
        output=output,
        no_overwrite=False,
        dry_run=False,
        no_mask=False
    )
    
    result = run_merge(args)
    assert result == 0
    
    merged = parse_env_file(output)
    assert merged['KEY1'] == 'overridden'
    assert merged['KEY2'] == 'value2'


def test_merge_dry_run_does_not_write(temp_dir, capsys):
    """Test that dry run shows output but doesn't write."""
    file1 = os.path.join(temp_dir, 'file1.env')
    output = os.path.join(temp_dir, 'merged.env')
    
    Path(file1).write_text('KEY1=value1\n')
    
    args = Namespace(
        files=[file1],
        output=output,
        no_overwrite=False,
        dry_run=True,
        no_mask=False
    )
    
    result = run_merge(args)
    assert result == 0
    assert not os.path.exists(output)
    
    captured = capsys.readouterr()
    assert 'Merged result' in captured.out
    assert 'Would write to' in captured.out


def test_merge_missing_file_returns_error(temp_dir, capsys):
    """Test that missing input file returns error."""
    output = os.path.join(temp_dir, 'merged.env')
    
    args = Namespace(
        files=['nonexistent.env'],
        output=output,
        no_overwrite=False,
        dry_run=False,
        no_mask=False
    )
    
    result = run_merge(args)
    assert result == 1
    
    captured = capsys.readouterr()
    assert 'File not found' in captured.err


def test_merge_no_overwrite_protects_existing(temp_dir, capsys):
    """Test that no-overwrite flag protects existing files."""
    file1 = os.path.join(temp_dir, 'file1.env')
    output = os.path.join(temp_dir, 'existing.env')
    
    Path(file1).write_text('KEY1=value1\n')
    Path(output).write_text('EXISTING=data\n')
    
    args = Namespace(
        files=[file1],
        output=output,
        no_overwrite=True,
        dry_run=False,
        no_mask=False
    )
    
    result = run_merge(args)
    assert result == 1
    
    # Original file should be unchanged
    original = parse_env_file(output)
    assert original == {'EXISTING': 'data'}
    
    captured = capsys.readouterr()
    assert 'already exists' in captured.err
