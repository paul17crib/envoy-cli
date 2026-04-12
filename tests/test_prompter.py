"""Tests for envoy.prompter."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from envoy.prompter import PromptAborted, confirm, prompt_missing, prompt_value


# ---------------------------------------------------------------------------
# prompt_value
# ---------------------------------------------------------------------------

def test_prompt_value_returns_entered_text():
    with patch("builtins.input", return_value="hello"):
        assert prompt_value("APP_NAME") == "hello"


def test_prompt_value_strips_whitespace():
    with patch("builtins.input", return_value="  spaced  "):
        assert prompt_value("KEY") == "spaced"


def test_prompt_value_uses_default_on_empty_input():
    with patch("builtins.input", return_value=""):
        assert prompt_value("KEY", default="fallback") == "fallback"


def test_prompt_value_explicit_entry_overrides_default():
    with patch("builtins.input", return_value="override"):
        assert prompt_value("KEY", default="fallback") == "override"


def test_prompt_value_secret_uses_getpass():
    with patch("getpass.getpass", return_value="s3cr3t") as mock_gp:
        result = prompt_value("DB_PASSWORD", secret=True)
    mock_gp.assert_called_once()
    assert result == "s3cr3t"


def test_prompt_value_eof_raises_aborted():
    with patch("builtins.input", side_effect=EOFError):
        with pytest.raises(PromptAborted):
            prompt_value("KEY")


# ---------------------------------------------------------------------------
# prompt_missing
# ---------------------------------------------------------------------------

def test_prompt_missing_fills_specified_keys():
    env = {"APP_NAME": "myapp", "SECRET_KEY": ""}
    with patch("envoy.prompter.prompt_value", side_effect=["newsecret"]):
        result = prompt_missing(env, ["SECRET_KEY"], sensitive_keys=["SECRET_KEY"])
    assert result["SECRET_KEY"] == "newsecret"
    assert result["APP_NAME"] == "myapp"


def test_prompt_missing_does_not_mutate_original():
    env = {"KEY": ""}
    with patch("envoy.prompter.prompt_value", return_value="value"):
        prompt_missing(env, ["KEY"])
    assert env["KEY"] == ""


def test_prompt_missing_passes_secret_flag_for_sensitive_keys():
    env = {"DB_PASS": ""}
    calls = []

    def fake_prompt(key, secret=False, default=None):
        calls.append((key, secret))
        return "val"

    with patch("envoy.prompter.prompt_value", side_effect=fake_prompt):
        prompt_missing(env, ["DB_PASS"], sensitive_keys=["DB_PASS"])

    assert calls[0] == ("DB_PASS", True)


# ---------------------------------------------------------------------------
# confirm
# ---------------------------------------------------------------------------

def test_confirm_yes_returns_true():
    with patch("builtins.input", return_value="y"):
        assert confirm("Continue?") is True


def test_confirm_no_returns_false():
    with patch("builtins.input", return_value="n"):
        assert confirm("Continue?") is False


def test_confirm_empty_uses_default_true():
    with patch("builtins.input", return_value=""):
        assert confirm("Continue?", default=True) is True


def test_confirm_empty_uses_default_false():
    with patch("builtins.input", return_value=""):
        assert confirm("Continue?", default=False) is False


def test_confirm_eof_raises_aborted():
    with patch("builtins.input", side_effect=EOFError):
        with pytest.raises(PromptAborted):
            confirm("Sure?")
