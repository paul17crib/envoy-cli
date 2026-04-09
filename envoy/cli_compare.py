import argparse
import sys
from envoy.sync import load_local, SyncError
from envoy.masker import mask_env
from envoy.cli_diff import print_diff
from envoy.remote import FileRemoteProvider, pull


def build_parser(subparsers=None):
    description = "Compare a local .env file against another local or remote file."
    if subparsers:
        parser = subparsers.add_parser("compare", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envoy compare", description=description)

    parser.add_argument(
        "--local",
        default=".env",
        help="Path to the local .env file (default: .env)",
    )
    parser.add_argument(
        "--against",
        required=True,
        help="Path to another local file or a remote URL/path to compare against.",
    )
    parser.add_argument(
        "--remote",
        action="store_true",
        help="Treat --against as a remote provider path.",
    )
    parser.add_argument(
        "--no-mask",
        action="store_true",
        help="Show sensitive values in plain text.",
    )
    return parser


def run_compare(args, stdout=None, stderr=None):
    out = stdout or sys.stdout
    err = stderr or sys.stderr

    try:
        local_env = load_local(args.local)
    except SyncError as e:
        err.write(f"Error loading local file: {e}\n")
        return 1

    try:
        if args.remote:
            provider = FileRemoteProvider(args.against)
            remote_env = pull(provider)
        else:
            remote_env = load_local(args.against)
    except SyncError as e:
        err.write(f"Error loading comparison file: {e}\n")
        return 1

    if not args.no_mask:
        local_env = mask_env(local_env)
        remote_env = mask_env(remote_env)

    out.write(f"Comparing {args.local} <-> {args.against}\n\n")
    print_diff(local_env, remote_env, file=out)
    return 0
