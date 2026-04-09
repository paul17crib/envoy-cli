"""Tests for the export command."""

import json
import pytest
from argparse import Namespace
from pathlib import Path

from envoy.cli_export import run_export, format_bash, format_docker, format_yaml


@pytest.fixture
def tmp_env_file(tmp_path):
    """Create a temporary .env file for testing."""
    env_file = tmp_path / '.env'
    env_file.write_text(
        'DATABASE_URL=postgres://localhost/mydb\n'
        'API_KEY=secret123\n'
        'APP_NAME=MyApp\n'
        'DEBUG=true\n'
    )
    return env_file


def test_export_bash_format(tmp_env_file, capsys):
    """Test exporting in bash format."""
    args = Namespace(file=str(tmp_env_file), format='bash', no_mask=True, prefix='')
    result = run_export(args)
    
    assert result == 0
    captured = capsys.readouterr()
    assert "export API_KEY='secret123'" in captured.out
    assert "export APP_NAME='MyApp'" in captured.out
    assert "export DATABASE_URL='postgres://localhost/mydb'" in captured.out
    assert "export DEBUG='true'" in captured.out


def test_export_json_format(tmp_env_file, capsys):
    """Test exporting in JSON format."""
    args = Namespace(file=str(tmp_env_file), format='json', no_mask=True, prefix='')
    result = run_export(args)
    
    assert result == 0
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output['API_KEY'] == 'secret123'
    assert output['APP_NAME'] == 'MyApp'
    assert output['DATABASE_URL'] == 'postgres://localhost/mydb'
    assert output['DEBUG'] == 'true'


def test_export_docker_format(tmp_env_file, capsys):
    """Test exporting in Docker format."""
    args = Namespace(file=str(tmp_env_file), format='docker', no_mask=True, prefix='')
    result = run_export(args)
    
    assert result == 0
    captured = capsys.readouterr()
    assert 'ENV API_KEY="secret123"' in captured.out
    assert 'ENV APP_NAME="MyApp"' in captured.out
    assert 'ENV DATABASE_URL="postgres://localhost/mydb"' in captured.out
    assert 'ENV DEBUG="true"' in captured.out


def test_export_yaml_format(tmp_env_file, capsys):
    """Test exporting in YAML format."""
    args = Namespace(file=str(tmp_env_file), format='yaml', no_mask=True, prefix='')
    result = run_export(args)
    
    assert result == 0
    captured = capsys.readouterr()
    assert 'API_KEY: secret123' in captured.out
    assert 'APP_NAME: MyApp' in captured.out
    assert 'DATABASE_URL: postgres://localhost/mydb' in captured.out
    assert 'DEBUG: true' in captured.out


def test_export_masks_sensitive_by_default(tmp_env_file, capsys):
    """Test that sensitive values are masked by default."""
    args = Namespace(file=str(tmp_env_file), format='bash', no_mask=False, prefix='')
    result = run_export(args)
    
    assert result == 0
    captured = capsys.readouterr()
    assert 'secret123' not in captured.out
    assert '***' in captured.out


def test_export_with_prefix(tmp_env_file, capsys):
    """Test exporting with a prefix."""
    args = Namespace(file=str(tmp_env_file), format='bash', no_mask=True, prefix='APP_')
    result = run_export(args)
    
    assert result == 0
    captured = capsys.readouterr()
    assert "export APP_API_KEY='secret123'" in captured.out
    assert "export APP_APP_NAME='MyApp'" in captured.out
    assert "export APP_DATABASE_URL='postgres://localhost/mydb'" in captured.out


def test_export_missing_file(capsys):
    """Test exporting a non-existent file."""
    args = Namespace(file='nonexistent.env', format='bash', no_mask=True, prefix='')
    result = run_export(args)
    
    assert result == 1
    captured = capsys.readouterr()
    assert 'not found' in captured.err


def test_format_bash_escapes_quotes():
    """Test that bash format properly escapes single quotes."""
    env_vars = {'KEY': "value with 'quotes'"}
    output = format_bash(env_vars)
    assert "export KEY='value with '\\''quotes'\\'''" in output


def test_format_docker_escapes_quotes():
    """Test that docker format properly escapes quotes."""
    env_vars = {'KEY': 'value with "quotes"'}
    output = format_docker(env_vars)
    assert 'ENV KEY="value with \\"quotes\\""' in output


def test_format_yaml_quotes_special_values():
    """Test that YAML format quotes values with special characters."""
    env_vars = {'KEY': '  leading space', 'KEY2': 'normal'}
    output = format_yaml(env_vars)
    assert 'KEY: "  leading space"' in output
    assert 'KEY2: normal' in output
