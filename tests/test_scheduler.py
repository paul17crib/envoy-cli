"""Tests for envoy.scheduler."""

import pytest
from envoy.scheduler import (
    ScheduledTask,
    SchedulerError,
    add_task,
    remove_task,
    toggle_task,
    get_task,
    load_schedules,
    save_schedules,
)


@pytest.fixture
def base_tasks():
    return [
        ScheduledTask(name="nightly-backup", action="backup", cron="0 2 * * *", env_file=".env"),
        ScheduledTask(name="daily-pull", action="pull", cron="0 6 * * *", env_file=".env"),
    ]


def test_add_task_appends_new_task(base_tasks):
    new = ScheduledTask(name="weekly-rotate", action="rotate", cron="0 0 * * 0", env_file=".env")
    result = add_task(base_tasks, new)
    assert len(result) == 3
    assert result[-1].name == "weekly-rotate"


def test_add_task_duplicate_name_raises(base_tasks):
    dup = ScheduledTask(name="nightly-backup", action="backup", cron="0 2 * * *", env_file=".env")
    with pytest.raises(SchedulerError, match="already exists"):
        add_task(base_tasks, dup)


def test_add_task_invalid_action_raises():
    task = ScheduledTask(name="bad", action="explode", cron="0 0 * * *", env_file=".env")
    with pytest.raises(SchedulerError, match="Unknown action"):
        add_task([], task)


def test_add_task_invalid_cron_raises():
    task = ScheduledTask(name="bad-cron", action="backup", cron="not-a-cron", env_file=".env")
    with pytest.raises(SchedulerError, match="Invalid cron"):
        add_task([], task)


def test_remove_task_removes_by_name(base_tasks):
    result = remove_task(base_tasks, "daily-pull")
    assert len(result) == 1
    assert result[0].name == "nightly-backup"


def test_remove_task_missing_raises(base_tasks):
    with pytest.raises(SchedulerError, match="not found"):
        remove_task(base_tasks, "nonexistent")


def test_toggle_task_disables(base_tasks):
    result = toggle_task(base_tasks, "nightly-backup", enabled=False)
    task = next(t for t in result if t.name == "nightly-backup")
    assert task.enabled is False


def test_toggle_task_enables(base_tasks):
    disabled = toggle_task(base_tasks, "daily-pull", enabled=False)
    re_enabled = toggle_task(disabled, "daily-pull", enabled=True)
    task = next(t for t in re_enabled if t.name == "daily-pull")
    assert task.enabled is True


def test_toggle_task_missing_raises(base_tasks):
    with pytest.raises(SchedulerError, match="not found"):
        toggle_task(base_tasks, "ghost", enabled=False)


def test_get_task_returns_correct(base_tasks):
    task = get_task(base_tasks, "daily-pull")
    assert task.action == "pull"


def test_get_task_missing_raises(base_tasks):
    with pytest.raises(SchedulerError, match="not found"):
        get_task(base_tasks, "missing")


def test_save_and_load_roundtrip(tmp_path):
    tasks = [
        ScheduledTask(name="t1", action="backup", cron="0 1 * * *", env_file=".env"),
        ScheduledTask(name="t2", action="push", cron="0 3 * * *", env_file=".env.prod", enabled=False),
    ]
    save_schedules(tasks, base=tmp_path)
    loaded = load_schedules(base=tmp_path)
    assert len(loaded) == 2
    assert loaded[0].name == "t1"
    assert loaded[1].enabled is False


def test_load_schedules_missing_file_returns_empty(tmp_path):
    result = load_schedules(base=tmp_path)
    assert result == []


def test_task_repr():
    t = ScheduledTask(name="x", action="pull", cron="* * * * *", env_file=".env")
    assert "x" in repr(t)
    assert "on" in repr(t)
