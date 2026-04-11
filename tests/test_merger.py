"""Tests for envoy.merger and envoy.cli_mmerge."""

import argparse
import pytest

from envoy.merger import (
    MergeConflictError,
    find_conflicts,
    keys_in_all,
    keys_in_any,
    merge_all,
)


# ---------------------------------------------------------------------------
# merge_all
# ---------------------------------------------------------------------------

def test_merge_all_empty_list_returns_empty():
    assert merge_all([]) == {}


def test_merge_all_single_env_returns_copy():
    env = {"A": "1", "B": "2"}
    assert merge_all([env]) == env


def test_merge_all_last_strategy_prefers_later_value():
    result = merge_all([{"X": "old"}, {"X": "new"}], strategy="last")
    assert result["X"] == "new"


def test_merge_all_first_strategy_prefers_earlier_value():
    result = merge_all([{"X": "old"}, {"X": "new"}], strategy="first")
    assert result["X"] == "old"


def test_merge_all_error_strategy_raises_on_conflict():
    with pytest.raises(MergeConflictError) as exc_info:
        merge_all([{"X": "a"}, {"X": "b"}], strategy="error")
    assert exc_info.value.key == "X"
    assert "a" in exc_info.value.values
    assert "b" in exc_info.value.values


def test_merge_all_error_strategy_no_raise_when_values_same():
    result = merge_all([{"X": "same"}, {"X": "same"}], strategy="error")
    assert result["X"] == "same"


def test_merge_all_combines_disjoint_keys():
    result = merge_all([{"A": "1"}, {"B": "2"}])
    assert result == {"A": "1", "B": "2"}


def test_merge_all_keys_filter_restricts_output():
    result = merge_all([{"A": "1", "B": "2", "C": "3"}], keys=["A", "C"])
    assert "B" not in result
    assert result["A"] == "1"
    assert result["C"] == "3"


# ---------------------------------------------------------------------------
# find_conflicts
# ---------------------------------------------------------------------------

def test_find_conflicts_detects_differing_values():
    conflicts = find_conflicts([{"K": "v1"}, {"K": "v2"}])
    assert "K" in conflicts
    assert set(conflicts["K"]) == {"v1", "v2"}


def test_find_conflicts_ignores_same_values():
    conflicts = find_conflicts([{"K": "same"}, {"K": "same"}])
    assert "K" not in conflicts


def test_find_conflicts_empty_envs_returns_empty():
    assert find_conflicts([]) == {}


# ---------------------------------------------------------------------------
# keys_in_all / keys_in_any
# ---------------------------------------------------------------------------

def test_keys_in_all_returns_common_keys():
    envs = [{"A": "1", "B": "2"}, {"A": "3", "C": "4"}]
    assert keys_in_all(envs) == ["A"]


def test_keys_in_any_returns_union():
    envs = [{"A": "1"}, {"B": "2"}]
    assert keys_in_any(envs) == ["A", "B"]


def test_keys_in_all_empty_returns_empty():
    assert keys_in_all([]) == []


# ---------------------------------------------------------------------------
# cli_mmerge
# ---------------------------------------------------------------------------

def test_run_mmerge_dry_run(tmp_path, capsys):
    from envoy.cli_mmerge import run_mmerge

    f1 = tmp_path / "a.env"
    f2 = tmp_path / "b.env"
    f1.write_text("FOO=bar\n")
    f2.write_text("BAZ=qux\n")

    args = argparse.Namespace(
        sources=[str(f1), str(f2)],
        output=str(tmp_path / "out.env"),
        strategy="last",
        keys=None,
        dry_run=True,
        no_overwrite=False,
        show_conflicts=False,
    )
    rc = run_mmerge(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "FOO=bar" in out
    assert "BAZ=qux" in out


def test_run_mmerge_missing_source_returns_error(tmp_path, capsys):
    from envoy.cli_mmerge import run_mmerge

    args = argparse.Namespace(
        sources=[str(tmp_path / "missing.env")],
        output=str(tmp_path / "out.env"),
        strategy="last",
        keys=None,
        dry_run=False,
        no_overwrite=False,
        show_conflicts=False,
    )
    rc = run_mmerge(args)
    assert rc == 1
