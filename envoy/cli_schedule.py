"""CLI interface for managing scheduled envoy tasks."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envoy.scheduler import (
    ScheduledTask,
    SchedulerError,
    add_task,
    remove_task,
    toggle_task,
    load_schedules,
    save_schedules,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy schedule",
        description="Manage scheduled envoy tasks (pull, push, backup, rotate).",
    )
    sub = parser.add_subparsers(dest="subcmd", required=True)

    add_p = sub.add_parser("add", help="Add a new scheduled task")
    add_p.add_argument("name", help="Unique task name")
    add_p.add_argument("--action", required=True, choices=["pull", "push", "backup", "rotate"])
    add_p.add_argument("--cron", required=True, help="Cron expression (5 fields)")
    add_p.add_argument("--file", dest="env_file", default=".env")
    add_p.add_argument("--disabled", action="store_true", default=False)

    rm_p = sub.add_parser("remove", help="Remove a scheduled task")
    rm_p.add_argument("name")

    ls_p = sub.add_parser("list", help="List all scheduled tasks")  # noqa: F841

    en_p = sub.add_parser("enable", help="Enable a task")
    en_p.add_argument("name")

    dis_p = sub.add_parser("disable", help="Disable a task")
    dis_p.add_argument("name")

    parser.add_argument("--schedule-dir", default=None, help="Directory for schedule file")
    return parser


def run_schedule(args: argparse.Namespace) -> int:
    base = Path(args.schedule_dir) if getattr(args, "schedule_dir", None) else None

    try:
        tasks = load_schedules(base=base)

        if args.subcmd == "add":
            task = ScheduledTask(
                name=args.name,
                action=args.action,
                cron=args.cron,
                env_file=args.env_file,
                enabled=not args.disabled,
            )
            tasks = add_task(tasks, task)
            save_schedules(tasks, base=base)
            print(f"[ok] Task {args.name!r} added ({args.action} @ {args.cron}).")

        elif args.subcmd == "remove":
            tasks = remove_task(tasks, args.name)
            save_schedules(tasks, base=base)
            print(f"[ok] Task {args.name!r} removed.")

        elif args.subcmd == "list":
            if not tasks:
                print("No scheduled tasks.")
            else:
                for t in tasks:
                    status = "enabled" if t.enabled else "disabled"
                    print(f"  {t.name:<24} {t.action:<10} {t.cron:<15} [{status}]  {t.env_file}")

        elif args.subcmd == "enable":
            tasks = toggle_task(tasks, args.name, enabled=True)
            save_schedules(tasks, base=base)
            print(f"[ok] Task {args.name!r} enabled.")

        elif args.subcmd == "disable":
            tasks = toggle_task(tasks, args.name, enabled=False)
            save_schedules(tasks, base=base)
            print(f"[ok] Task {args.name!r} disabled.")

    except SchedulerError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    return 0
