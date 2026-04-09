import argparse
import sys

from envoy.cli_init import build_parser as init_parser, run_init
from envoy.cli_show import build_parser as show_parser, run_show
from envoy.cli_pull import build_parser as pull_parser, run_pull
from envoy.cli_push import build_parser as push_parser, run_push
from envoy.cli_diff import build_parser as diff_parser, run_diff  # noqa: F401 (may not exist yet)
from envoy.cli_validate import run_validate
from envoy.cli_edit import build_parser as edit_parser, run_edit
from envoy.cli_merge import build_parser as merge_parser, run_merge
from envoy.cli_export import build_parser as export_parser, run_export
from envoy.cli_backup import build_parser as backup_parser, run_backup
from envoy.cli_set import build_parser as set_parser, run_set
from envoy.cli_unset import build_parser as unset_parser, run_unset
from envoy.cli_copy import build_parser as copy_parser, run_copy
from envoy.cli_rename import build_parser as rename_parser, run_rename
from envoy.cli_rotate import build_parser as rotate_parser, run_rotate
from envoy.cli_compare import build_parser as compare_parser, run_compare


COMMANDS = {
    "init": (init_parser, run_init),
    "show": (show_parser, run_show),
    "pull": (pull_parser, run_pull),
    "push": (push_parser, run_push),
    "edit": (edit_parser, run_edit),
    "merge": (merge_parser, run_merge),
    "export": (export_parser, run_export),
    "backup": (backup_parser, run_backup),
    "set": (set_parser, run_set),
    "unset": (unset_parser, run_unset),
    "copy": (copy_parser, run_copy),
    "rename": (rename_parser, run_rename),
    "rotate": (rotate_parser, run_rotate),
    "compare": (compare_parser, run_compare),
}


def build_main_parser():
    parser = argparse.ArgumentParser(
        prog="envoy",
        description="Manage and sync .env files across environments.",
    )
    parser.add_argument(
        "--version", action="version", version="%(prog)s 0.1.0"
    )
    subparsers = parser.add_subparsers(dest="command", metavar="<command>")

    for name, (builder, _) in COMMANDS.items():
        builder(subparsers)

    return parser


def main(argv=None):
    parser = build_main_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    _, runner = COMMANDS[args.command]
    return runner(args) or 0


if __name__ == "__main__":
    sys.exit(main())
