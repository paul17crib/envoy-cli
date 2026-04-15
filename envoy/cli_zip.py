"""CLI command: envoy zip / unzip — combine or split paired env values."""
from __future__ import annotations

import argparse
import sys

from envoy.sync import load_local, save_local, SyncError
from envoy.zipper import zip_envs, unzip_env, get_zipped_keys, ZipperError


def build_parser(subparsers=None):
    desc = "Zip two .env files together or unzip a combined file."
    if subparsers is not None:
        parser = subparsers.add_parser("zip", help=desc, description=desc)
    else:
        parser = argparse.ArgumentParser(prog="envoy zip", description=desc)

    sub = parser.add_subparsers(dest="zip_cmd", required=True)

    # zip sub-command
    p_zip = sub.add_parser("merge", help="Combine two env files into one.")
    p_zip.add_argument("left", help="Left / base .env file.")
    p_zip.add_argument("right", help="Right .env file whose values are appended.")
    p_zip.add_argument("--output", "-o", default=None, help="Output file (default: stdout).")
    p_zip.add_argument("--delimiter", "-d", default="|", help="Value separator (default: '|').")
    p_zip.add_argument("--keys", nargs="+", default=None, metavar="KEY", help="Only zip these keys.")
    p_zip.add_argument("--dry-run", action="store_true", help="Print result without writing.")

    # unzip sub-command
    p_unzip = sub.add_parser("split", help="Split a zipped env file into two files.")
    p_unzip.add_argument("file", help="Zipped .env file to split.")
    p_unzip.add_argument("--left-output", default=None, help="Output for left side (default: stdout).")
    p_unzip.add_argument("--right-output", default=None, help="Output for right side (default: stdout).")
    p_unzip.add_argument("--delimiter", "-d", default="|", help="Value separator (default: '|').")
    p_unzip.add_argument("--keys", nargs="+", default=None, metavar="KEY", help="Only split these keys.")
    p_unzip.add_argument("--list", dest="list_only", action="store_true", help="List zipped keys only.")

    return parser


def run_zip(args) -> int:
    try:
        if args.zip_cmd == "merge":
            left_env = load_local(args.left)
            right_env = load_local(args.right)
            result = zip_envs(left_env, right_env, delimiter=args.delimiter, keys=args.keys)
            if args.dry_run or args.output is None:
                for k, v in result.items():
                    print(f"{k}={v}")
            else:
                save_local(args.output, result, overwrite=True)
                print(f"Zipped env written to {args.output}")
            return 0

        elif args.zip_cmd == "split":
            env = load_local(args.file)
            if args.list_only:
                zipped = get_zipped_keys(env, delimiter=args.delimiter)
                if zipped:
                    print("\n".join(zipped))
                else:
                    print("No zipped keys found.")
                return 0

            left, right = unzip_env(env, delimiter=args.delimiter, keys=args.keys)

            if args.left_output:
                save_local(args.left_output, left, overwrite=True)
                print(f"Left side written to {args.left_output}")
            else:
                print("--- LEFT ---")
                for k, v in left.items():
                    print(f"{k}={v}")

            if args.right_output:
                save_local(args.right_output, right, overwrite=True)
                print(f"Right side written to {args.right_output}")
            else:
                print("--- RIGHT ---")
                for k, v in right.items():
                    print(f"{k}={v}")

            return 0

    except (SyncError, ZipperError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
