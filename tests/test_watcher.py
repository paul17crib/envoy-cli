"""Tests for envoy.watcher."""

import os
import time
import pytest

from envoy.watcher import watch_once, WatchEvent, watch
from envoy.parser import serialize_env


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("APP_NAME=envoy\nDEBUG=false\n")
    return p


def test_watch_once_no_changes(env_file):
    previous = {"APP_NAME": "envoy", "DEBUG": "false"}
    event = watch_once(str(env_file), previous)
    assert not event.has_changes()
    assert event.current == previous


def test_watch_once_detects_added_key(env_file):
    previous = {"APP_NAME": "envoy"}
    event = watch_once(str(env_file), previous)
    assert event.has_changes()
    symbols = {c.symbol for c in event.changes}
    assert "+" in symbols


def test_watch_once_detects_removed_key(env_file):
    previous = {"APP_NAME": "envoy", "DEBUG": "false", "EXTRA": "gone"}
    event = watch_once(str(env_file), previous)
    removed = [c for c in event.changes if c.symbol == "-"]
    assert any(c.key == "EXTRA" for c in removed)


def test_watch_once_detects_changed_value(env_file):
    previous = {"APP_NAME": "old", "DEBUG": "false"}
    event = watch_once(str(env_file), previous)
    changed = [c for c in event.changes if c.symbol == "~"]
    assert any(c.key == "APP_NAME" for c in changed)


def test_watch_once_missing_file():
    event = watch_once("/nonexistent/.env", {"A": "1"})
    assert event.current == {}


def test_watch_event_timestamp():
    before = time.time()
    event = WatchEvent(path="x", previous={}, current={}, changes=[])
    assert event.timestamp >= before


def test_watch_event_has_changes_false():
    event = WatchEvent(path="x", previous={}, current={}, changes=[])
    assert not event.has_changes()


def test_watch_event_has_changes_true():
    from envoy.differ import DiffEntry
    entry = DiffEntry(key="K", symbol="+", old_value=None, new_value="v")
    event = WatchEvent(path="x", previous={}, current={"K": "v"}, changes=[entry])
    assert event.has_changes()


def test_watch_calls_callback_on_change(tmp_path):
    p = tmp_path / ".env"
    p.write_text("A=1\n")
    events = []

    def cb(e):
        events.append(e)

    # Run 2 iterations: first no change, second after writing new content
    original_sleep = time.sleep
    call_count = [0]

    def fake_sleep(n):
        call_count[0] += 1
        if call_count[0] == 1:
            p.write_text("A=2\n")

    import unittest.mock as mock
    with mock.patch("envoy.watcher.time.sleep", side_effect=fake_sleep):
        watch(str(p), cb, interval=0.01, max_iterations=2)

    assert len(events) == 1
    assert events[0].has_changes()
