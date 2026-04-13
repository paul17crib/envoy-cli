"""Tests for envoy.cli_watch."""

import argparse
import pytest
from unittest import mock

from envoy.cli_watch import build_parser, run_watch, _format_event
from envoy.watcher import WatchEvent
from envoy.differ import DiffEntry


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("SECRET_KEY=abc123\nDEBUG=true\n")
    return p


def make_args(**kwargs) -> argparse.Namespace:
    defaults = {"file": ".env", "interval": 1.0, "no_mask": False, "once": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_parser_returns_parser():
    parser = build_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_build_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["myfile.env"])
    assert args.file == "myfile.env"
    assert args.interval == 1.0
    assert args.no_mask is False
    assert args.once is False


def test_run_watch_once_no_changes(env_file, capsys):
    args = make_args(file=str(env_file), once=True)
    ret = run_watch(args)
    assert ret == 0


def test_run_watch_once_missing_file(capsys):
    args = make_args(file="/nonexistent/.env", once=True)
    ret = run_watch(args)
    assert ret == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_format_event_added_key():
    entry = DiffEntry(key="NEW_KEY", symbol="+", old_value=None, new_value="hello")
    event = WatchEvent(
        path=".env",
        previous={},
        current={"NEW_KEY": "hello"},
        changes=[entry],
    )
    lines = _format_event(event, mask=False)
    assert any("+" in l and "NEW_KEY" in l for l in lines)


def test_format_event_removed_key():
    entry = DiffEntry(key="OLD", symbol="-", old_value="x", new_value=None)
    event = WatchEvent(
        path=".env",
        previous={"OLD": "x"},
        current={},
        changes=[entry],
    )
    lines = _format_event(event, mask=False)
    assert any("-" in l and "OLD" in l for l in lines)


def test_format_event_masks_sensitive_values():
    entry = DiffEntry(key="SECRET_KEY", symbol="~", old_value="old", new_value="new")
    event = WatchEvent(
        path=".env",
        previous={"SECRET_KEY": "old"},
        current={"SECRET_KEY": "new"},
        changes=[entry],
    )
    lines = _format_event(event, mask=True)
    assert not any("new" in l for l in lines)
    assert any("SECRET_KEY" in l for l in lines)


def test_run_watch_polls_until_keyboard_interrupt(env_file, capsys):
    args = make_args(file=str(env_file), interval=0.01)
    with mock.patch("envoy.cli_watch.watch", side_effect=KeyboardInterrupt):
        ret = run_watch(args)
    assert ret == 0
    captured = capsys.readouterr()
    assert "Stopped" in captured.out
