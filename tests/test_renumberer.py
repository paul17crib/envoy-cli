"""Unit tests for envoy.renumberer."""

import pytest

from envoy.renumberer import (
    RenumbererError,
    find_gaps,
    get_renumber_preview,
    renumber_prefix,
)


@pytest.fixture
def gapped_env():
    return {
        "ITEM_1": "alpha",
        "ITEM_3": "gamma",
        "ITEM_5": "epsilon",
        "OTHER": "unchanged",
    }


def test_find_gaps_detects_missing_indices(gapped_env):
    assert find_gaps(gapped_env, "ITEM") == [2, 4]


def test_find_gaps_no_gaps_returns_empty():
    env = {"ITEM_1": "a", "ITEM_2": "b", "ITEM_3": "c"}
    assert find_gaps(env, "ITEM") == []


def test_find_gaps_unknown_prefix_returns_empty(gapped_env):
    assert find_gaps(gapped_env, "MISSING") == []


def test_renumber_prefix_closes_gaps(gapped_env):
    result = renumber_prefix(gapped_env, "ITEM")
    assert list(result.keys()) == ["OTHER", "ITEM_1", "ITEM_2", "ITEM_3"]


def test_renumber_prefix_preserves_values(gapped_env):
    result = renumber_prefix(gapped_env, "ITEM")
    assert result["ITEM_1"] == "alpha"
    assert result["ITEM_2"] == "gamma"
    assert result["ITEM_3"] == "epsilon"


def test_renumber_prefix_preserves_unrelated_keys(gapped_env):
    result = renumber_prefix(gapped_env, "ITEM")
    assert result["OTHER"] == "unchanged"


def test_renumber_prefix_custom_start(gapped_env):
    result = renumber_prefix(gapped_env, "ITEM", start=0)
    assert "ITEM_0" in result
    assert "ITEM_1" in result
    assert "ITEM_2" in result


def test_renumber_prefix_no_matching_keys():
    env = {"FOO": "bar"}
    result = renumber_prefix(env, "ITEM")
    assert result == env


def test_renumber_prefix_empty_prefix_raises():
    with pytest.raises(RenumbererError):
        renumber_prefix({"ITEM_1": "x"}, "")


def test_renumber_prefix_does_not_mutate_original(gapped_env):
    original = dict(gapped_env)
    renumber_prefix(gapped_env, "ITEM")
    assert gapped_env == original


def test_get_renumber_preview_returns_changed_pairs(gapped_env):
    preview = get_renumber_preview(gapped_env, "ITEM")
    old_keys = [p[0] for p in preview]
    new_keys = [p[1] for p in preview]
    assert "ITEM_3" in old_keys
    assert "ITEM_2" in new_keys


def test_get_renumber_preview_no_change_if_contiguous():
    env = {"ITEM_1": "a", "ITEM_2": "b"}
    assert get_renumber_preview(env, "ITEM") == []


def test_renumber_case_insensitive_prefix():
    env = {"item_1": "a", "item_3": "b"}
    result = renumber_prefix(env, "item")
    assert "item_2" in result
