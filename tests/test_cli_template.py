import pytest
import argparse
from pathlib import Path
from envoy.cli_template import build_parser, render_template, run_template


@pytest.fixture
def tmp_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("APP_NAME=MyApp\nDB_HOST=localhost\nSECRET_KEY=supersecret\n")
    return env_file


@pytest.fixture
def tmp_template_file(tmp_path):
    tmpl = tmp_path / "config.tmpl"
    tmpl.write_text("app: {{APP_NAME}}\ndb: {{DB_HOST}}\nport: 5432\n")
    return tmpl


def make_args(template, env=".env", output=None, strict=False):
    return argparse.Namespace(template=str(template), env=str(env), output=output, strict=strict)


# --- render_template unit tests ---

def test_render_template_substitutes_known_keys():
    result, missing = render_template("Hello {{NAME}}!", {"NAME": "World"})
    assert result == "Hello World!"
    assert missing == []


def test_render_template_leaves_unknown_placeholder_intact():
    result, missing = render_template("{{UNKNOWN}}", {})
    assert "{{UNKNOWN}}" in result
    assert "UNKNOWN" in missing


def test_render_template_multiple_placeholders():
    text = "{{A}} and {{B}} and {{A}}"
    result, missing = render_template(text, {"A": "foo", "B": "bar"})
    assert result == "foo and bar and foo"
    assert missing == []


def test_render_template_handles_spaces_in_placeholder():
    result, missing = render_template("{{ KEY }}", {"KEY": "value"})
    assert result == "value"
    assert missing == []


def test_render_template_reports_all_missing_keys():
    _, missing = render_template("{{X}} {{Y}} {{Z}}", {})
    assert set(missing) == {"X", "Y", "Z"}


# --- run_template integration tests ---

def test_template_renders_to_stdout(tmp_env_file, tmp_template_file, capsys):
    args = make_args(tmp_template_file, env=tmp_env_file)
    rc = run_template(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "MyApp" in out
    assert "localhost" in out


def test_template_renders_to_output_file(tmp_env_file, tmp_template_file, tmp_path):
    out_file = tmp_path / "rendered.txt"
    args = make_args(tmp_template_file, env=tmp_env_file, output=str(out_file))
    rc = run_template(args)
    assert rc == 0
    content = out_file.read_text()
    assert "MyApp" in content
    assert "localhost" in content


def test_template_missing_env_file_returns_error(tmp_template_file, capsys):
    args = make_args(tmp_template_file, env="/nonexistent/.env")
    rc = run_template(args)
    assert rc == 1
    assert "not found" in capsys.readouterr().out


def test_template_missing_template_file_returns_error(tmp_env_file, capsys):
    args = make_args("/nonexistent/template.tmpl", env=tmp_env_file)
    rc = run_template(args)
    assert rc == 1
    assert "not found" in capsys.readouterr().out


def test_template_strict_mode_fails_on_missing_key(tmp_env_file, tmp_path, capsys):
    tmpl = tmp_path / "strict.tmpl"
    tmpl.write_text("value: {{MISSING_KEY}}\n")
    args = make_args(tmpl, env=tmp_env_file, strict=True)
    rc = run_template(args)
    assert rc == 1
    out = capsys.readouterr().out
    assert "MISSING_KEY" in out


def test_template_non_strict_warns_but_succeeds(tmp_env_file, tmp_path, capsys):
    tmpl = tmp_path / "warn.tmpl"
    tmpl.write_text("value: {{MISSING_KEY}}\n")
    args = make_args(tmpl, env=tmp_env_file, strict=False)
    rc = run_template(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "warn" in out.lower() or "MISSING_KEY" in out
