import json
import pytest
from unittest.mock import patch
from types import SimpleNamespace
from envoy.cli_stats import build_parser, collect_stats, run_stats


@pytest.fixture
def tmp_env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text(
        "APP_NAME=myapp\n"
        "SECRET_KEY=supersecret\n"
        "API_TOKEN=\n"
        "DB_PASSWORD=short\n"
        "DEBUG=true\n"
    )
    return str(f)


def make_args(file, as_json=False):
    return SimpleNamespace(file=file, as_json=as_json)


def test_collect_stats_counts_total():
    env = {"APP_NAME": "app", "SECRET_KEY": "abc", "EMPTY": ""}
    stats = collect_stats(env)
    assert stats["total_keys"] == 3


def test_collect_stats_counts_sensitive():
    env = {"SECRET_KEY": "val", "API_TOKEN": "tok", "APP": "app"}
    stats = collect_stats(env)
    assert stats["sensitive_keys"] == 2
    assert "SECRET_KEY" in stats["sensitive_key_names"]
    assert "API_TOKEN" in stats["sensitive_key_names"]


def test_collect_stats_counts_empty():
    env = {"A": "", "B": "", "C": "value"}
    stats = collect_stats(env)
    assert stats["empty_values"] == 2
    assert "A" in stats["empty_key_names"]
    assert "B" in stats["empty_key_names"]


def test_collect_stats_no_issues_on_clean_env():
    env = {"APP": "myapp", "PORT": "8080"}
    stats = collect_stats(env)
    assert stats["audit_errors"] == 0
    assert stats["empty_values"] == 0


def test_run_stats_missing_file_returns_error(tmp_path):
    args = make_args(str(tmp_path / "missing.env"))
    result = run_stats(args)
    assert result == 1


def test_run_stats_prints_summary(tmp_env_file, capsys):
    args = make_args(tmp_env_file)
    result = run_stats(args)
    captured = capsys.readouterr()
    assert result == 0
    assert "Total keys" in captured.out
    assert "Sensitive keys" in captured.out


def test_run_stats_json_output(tmp_env_file, capsys):
    args = make_args(tmp_env_file, as_json=True)
    result = run_stats(args)
    captured = capsys.readouterr()
    assert result == 0
    data = json.loads(captured.out)
    assert "total_keys" in data
    assert "sensitive_keys" in data
    assert "empty_values" in data
    assert "audit_errors" in data
    assert "audit_warnings" in data


def test_run_stats_json_sensitive_key_names(tmp_env_file, capsys):
    args = make_args(tmp_env_file, as_json=True)
    run_stats(args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data["sensitive_key_names"], list)
    assert "SECRET_KEY" in data["sensitive_key_names"]


def test_run_stats_shows_empty_key_names(tmp_env_file, capsys):
    args = make_args(tmp_env_file)
    run_stats(args)
    captured = capsys.readouterr()
    assert "API_TOKEN" in captured.out


def test_build_parser_defaults():
    parser = build_parser()
    args = parser.parse_args([])
    assert args.file == ".env"
    assert args.as_json is False
