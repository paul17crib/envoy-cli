"""Tests for envoy.planner and envoy.cli_plan."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envoy.planner import (
    MigrationPlan,
    PlanStep,
    apply_plan,
    build_plan,
)


# ---------------------------------------------------------------------------
# build_plan
# ---------------------------------------------------------------------------

def test_build_plan_detects_addition():
    plan = build_plan({"A": "1"}, {"A": "1", "B": "2"})
    adds = plan.by_action("add")
    assert len(adds) == 1
    assert adds[0].key == "B"
    assert adds[0].new_value == "2"


def test_build_plan_detects_removal():
    plan = build_plan({"A": "1", "B": "2"}, {"A": "1"})
    removes = plan.by_action("remove")
    assert len(removes) == 1
    assert removes[0].key == "B"


def test_build_plan_detects_update():
    plan = build_plan({"A": "old"}, {"A": "new"})
    updates = plan.by_action("update")
    assert len(updates) == 1
    assert updates[0].old_value == "old"
    assert updates[0].new_value == "new"


def test_build_plan_unchanged_key_not_included():
    plan = build_plan({"A": "1"}, {"A": "1"})
    assert plan.is_empty


def test_build_plan_rename_creates_rename_step():
    plan = build_plan({"OLD": "val"}, {"NEW": "val"}, renames={"OLD": "NEW"})
    renames = plan.by_action("rename")
    assert len(renames) == 1
    assert renames[0].key == "OLD"
    assert renames[0].new_key == "NEW"
    # Should NOT appear as add/remove
    assert not plan.by_action("add")
    assert not plan.by_action("remove")


def test_build_plan_empty_envs_returns_empty_plan():
    plan = build_plan({}, {})
    assert plan.is_empty


def test_plan_by_action_filters_correctly():
    plan = build_plan({"X": "1"}, {"Y": "2"})
    assert plan.by_action("remove")
    assert plan.by_action("add")
    assert not plan.by_action("update")


# ---------------------------------------------------------------------------
# apply_plan
# ---------------------------------------------------------------------------

def test_apply_plan_adds_key():
    plan = MigrationPlan(steps=[PlanStep(action="add", key="B", new_value="2")])
    result = apply_plan({"A": "1"}, plan)
    assert result["B"] == "2"
    assert result["A"] == "1"


def test_apply_plan_removes_key():
    plan = MigrationPlan(steps=[PlanStep(action="remove", key="A", old_value="1")])
    result = apply_plan({"A": "1", "B": "2"}, plan)
    assert "A" not in result
    assert result["B"] == "2"


def test_apply_plan_updates_key():
    plan = MigrationPlan(steps=[PlanStep(action="update", key="A", old_value="old", new_value="new")])
    result = apply_plan({"A": "old"}, plan)
    assert result["A"] == "new"


def test_apply_plan_renames_key():
    plan = MigrationPlan(steps=[PlanStep(action="rename", key="OLD", new_key="NEW", old_value="v")])
    result = apply_plan({"OLD": "v"}, plan)
    assert "OLD" not in result
    assert result["NEW"] == "v"


def test_apply_plan_does_not_mutate_original():
    env = {"A": "1"}
    plan = MigrationPlan(steps=[PlanStep(action="add", key="B", new_value="2")])
    apply_plan(env, plan)
    assert "B" not in env


# ---------------------------------------------------------------------------
# PlanStep repr
# ---------------------------------------------------------------------------

def test_plan_step_repr_add():
    assert "add" in repr(PlanStep(action="add", key="K", new_value="v"))


def test_plan_step_repr_rename():
    r = repr(PlanStep(action="rename", key="OLD", new_key="NEW"))
    assert "OLD" in r and "NEW" in r
