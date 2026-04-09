import argparse
import sys
from envoy.cli_pull import run_pull, build_parser as pull_parser
from envoy.cli_push import run_push, build_parser as push_parser
from envoy.cli_diff import run_diff
from envoy.cli_validate import run_validate


def build_main_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy",
        description="Manage and sync .env files across environments.",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="<command>")

    subparsers.add_parser(
        "pull",
        parents=[pull_parser()],
        add_help=False,
        help="Pull .env from a remote provider",
    )
    subparsers.add_parser(
        "push",
        parents=[push_parser()],
        add_help=False,
        help="Push local .env to a remote provider",
    )

    diff_p = subparsers.add_parser("diff", help="Diff two .env files")
    diff_p.add_argument("file_a", help="First .env file")
    diff_p.add_argument("file_b", help="Second .env file")
    diff_p.add_argument("--no-color", action="store_true", help="Disable color output")

    validate_p = subparsers.add_parser("validate", help="Validate a .env file")
    validate_p.add_argument("--file", "-f", default=".env", help="File to validate")

    return parser


def main(argv=None) -> int:
    parser = build_main_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "pull":
        return run_pull(args)
    elif args.command == "push":
        return run_push(args)
    elif args.command == "diff":
        return run_diff(args)
    elif args.command == "validate":
        return run_validate(args)
    else:
        print(f"[error] Unknown command: {args.command}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
