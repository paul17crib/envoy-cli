"""CLI commands for archiving and extracting .env files."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional

from envoy.archiver import ArchiveError, archive_env_files, extract_env_archive, list_archive_contents


def build_parser(parent: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:
    desc = "Archive or extract .env files into/from a zip bundle."
    if parent is not None:
        parser = parent.add_parser("archive", help=desc)
    else:
        parser = argparse.ArgumentParser(prog="envoy archive", description=desc)

    sub = parser.add_subparsers(dest="archive_cmd", required=True)

    # create sub-command
    create_p = sub.add_parser("create", help="Bundle .env files into a zip archive.")
    create_p.add_argument("files", nargs="+", help=".env files to archive")
    create_p.add_argument("-o", "--output", required=True, help="Destination zip file")
    create_p.add_argument("--mask", action="store_true", help="Mask sensitive values before archiving")
    create_p.add_argument("--no-manifest", action="store_true", help="Omit manifest.json from archive")

    # extract sub-command
    extract_p = sub.add_parser("extract", help="Extract .env files from a zip archive.")
    extract_p.add_argument("archive", help="Zip archive to extract")
    extract_p.add_argument("-d", "--dest", default=".", help="Destination directory (default: current dir)")

    # list sub-command
    list_p = sub.add_parser("list", help="List contents of a zip archive.")
    list_p.add_argument("archive", help="Zip archive to inspect")

    return parser


def run_archive(args: argparse.Namespace) -> int:
    try:
        if args.archive_cmd == "create":
            paths = [Path(f) for f in args.files]
            dest = Path(args.output)
            entries = archive_env_files(
                paths,
                dest,
                mask=args.mask,
                include_manifest=not args.no_manifest,
            )
            print(f"Archived {len(entries)} file(s) to {dest}")
            for e in entries:
                print(f"  + {e}")
            return 0

        elif args.archive_cmd == "extract":
            src = Path(args.archive)
            dest_dir = Path(args.dest)
            extracted = extract_env_archive(src, dest_dir)
            print(f"Extracted {len(extracted)} file(s) to {dest_dir}")
            for p in extracted:
                print(f"  -> {p}")
            return 0

        elif args.archive_cmd == "list":
            src = Path(args.archive)
            entries = list_archive_contents(src)
            if not entries:
                print("Archive is empty.")
            else:
                print(f"Contents of {src} ({len(entries)} file(s)):")
                for e in entries:
                    print(f"  {e}")
            return 0

    except ArchiveError as exc:
        print(f"Error: {exc}")
        return 1

    return 0
