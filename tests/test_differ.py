"""Tests for envoy.differ module."""

import pytest
from envoy.differ import compute_diff, diff_summary, DiffEntry


BASE = {"A": "1", "B": "2", "C": "3"}
TARGET = {"A": "1", "B": "99", "D": "4"}


def test_added_key_has_plus_symbol():
    entries = compute_diff(BASE, TARGET)
    added = [e for e in entries if e.key == "D"]
    assert len(added) == 1
    assert added[0].symbol == "+"
    assert added[0].new_value == "4"
    assert added[0].old_value is None


def test_removed_key_has_minus_symbol():
    entries = compute_diff(BASE, TARGET)
    removed = [e for e in entries if e.key == "C"]
    assert len(removed) == 1
    assert removed[0].symbol == "-"
    assert removed[0].old_value == "3"
    assert removed[0].new_value is None


def test_changed_key_has_tilde_symbol():
    entries = compute_diff(BASE, TARGET)
    changed = [e for e in entries if e.key == "B"]
    assert len(changed) == 1
    assert changed[0].symbol == "~"
    assert changed[0].old_value == "2"
    assert changed[0].new_value == "99"


def test_unchanged_excluded_by_default():
    entries = compute_diff(BASE, TARGET)
    unchanged = [e for e in entries if e.key == "A"]
    assert unchanged == []


def test_unchanged_included_when_flag_set():
    entries = compute_diff(BASE, TARGET, include_unchanged=True)
    unchanged = [e for e in entries if e.key == "A"]
    assert len(unchanged) == 1
    assert unchanged[0].symbol == "="


def test_entries_sorted_by_key():
    entries = compute_diff(BASE, TARGET)
    keys = [e.key for e in entries]
    assert keys == sorted(keys)


def test_identical_dicts_returns_empty():
    entries = compute_diff(BASE, BASE)
    assert entries == []


def test_empty_base_all_added():
    entries = compute_diff({}, {"X": "1", "Y": "2"})
    assert all(e.symbol == "+" for e in entries)
    assert len(entries) == 2


def test_empty_target_all_removed():
    entries = compute_diff({"X": "1", "Y": "2"}, {})
    assert all(e.symbol == "-" for e in entries)


def test_diff_summary_counts():
    entries = compute_diff(BASE, TARGET)
    added, removed, changed = diff_summary(entries)
    assert added == 1
    assert removed == 1
    assert changed == 1


def test_diff_summary_empty():
    added, removed, changed = diff_summary([])
    assert (added, removed, changed) == (0, 0, 0)


def test_diff_entry_properties():
    e_add = DiffEntry("K", "+", None, "v")
    assert e_add.is_added
    assert not e_add.is_removed

    e_rem = DiffEntry("K", "-", "v", None)
    assert e_rem.is_removed

    e_chg = DiffEntry("K", "~", "a", "b")
    assert e_chg.is_changed

    e_unc = DiffEntry("K", "=", "v", "v")
    assert e_unc.is_unchanged
