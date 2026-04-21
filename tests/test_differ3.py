"""Tests for envoy.differ3 (three-way diff)."""
import pytest
from envoy.differ3 import ThreeWayEntry, three_way_diff


def test_equal_entry_has_no_conflict():
    e = ThreeWayEntry(key="K", base="v", ours="v", theirs="v")
    assert not e.has_conflict
    assert e.symbol == "="


def test_only_ours_changed_no_conflict():
    e = ThreeWayEntry(key="K", base="old", ours="new", theirs="old")
    assert not e.has_conflict
    assert e.symbol == "~"


def test_only_theirs_changed_no_conflict():
    e = ThreeWayEntry(key="K", base="old", ours="old", theirs="new")
    assert not e.has_conflict


def test_both_changed_differently_is_conflict():
    e = ThreeWayEntry(key="K", base="old", ours="A", theirs="B")
    assert e.has_conflict
    assert e.symbol == "!"


def test_ours_deleted_theirs_changed_is_conflict():
    e = ThreeWayEntry(key="K", base="v", ours=None, theirs="new")
    assert e.has_conflict


def test_ours_absent_theirs_present_symbol_minus():
    e = ThreeWayEntry(key="K", base=None, ours=None, theirs="v")
    assert not e.has_conflict
    assert e.symbol == "+"


def test_ours_present_theirs_absent_symbol_plus():
    e = ThreeWayEntry(key="K", base=None, ours="v", theirs=None)
    assert not e.has_conflict
    assert e.symbol == "-"


def test_three_way_diff_keys_sorted():
    base = {"B": "1", "A": "2"}
    ours = {"B": "1", "A": "2"}
    theirs = {"B": "1", "A": "2"}
    report = three_way_diff(base, ours, theirs)
    assert [e.key for e in report.entries] == ["A", "B"]


def test_three_way_diff_detects_conflict():
    base = {"X": "old"}
    ours = {"X": "mine"}
    theirs = {"X": "yours"}
    report = three_way_diff(base, ours, theirs)
    assert report.has_conflicts
    assert "X" in report.conflict_keys


def test_three_way_diff_no_conflict_when_same_change():
    base = {"X": "old"}
    ours = {"X": "new"}
    theirs = {"X": "new"}
    report = three_way_diff(base, ours, theirs)
    assert not report.has_conflicts


def test_three_way_diff_auto_resolved_excludes_conflicts():
    base = {"A": "1", "B": "2"}
    ours = {"A": "changed", "B": "conflict-ours"}
    theirs = {"A": "1", "B": "conflict-theirs"}
    report = three_way_diff(base, ours, theirs)
    resolved = report.auto_resolved()
    assert "A" in resolved
    assert "B" not in resolved


def test_three_way_diff_all_keys_collected():
    base = {"A": "1"}
    ours = {"A": "1", "B": "2"}
    theirs = {"A": "1", "C": "3"}
    report = three_way_diff(base, ours, theirs)
    keys = {e.key for e in report.entries}
    assert keys == {"A", "B", "C"}
