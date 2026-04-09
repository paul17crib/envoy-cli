import argparse
import sys
from pathlib import Path
from envoy.sync import load_local, save_local, SyncError
from envoy.masker import is_sensitive_key
from envoy.rotator import rotate_env, RotationPlan


def build_parser(subparsers=None):
    description = "Rotate sensitive values in a .env file"
    if subparsers:
        parser = subparsers.add_parser("rotate", help=description)
    else:
        parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "--file", default=".env", help="Path to the .env file (default: .env)"
    )
    parser.add_argument(
        "--keys",
        nargs="+",
        metavar="KEY",
        help="Specific keys to rotate (default: all sensitive keys)",
    )
    parser.add_argument(
        "--length",
        type=int,
        default=32,
        help="Length of generated secret values (default: 32)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview which keys would be rotated without writing changes",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create a backup of the original file before rotating",
    )
    return parser


def run_rotate(args, out=sys.stdout, err=sys.stderr):
    try:
        env = load_local(args.file)
    except SyncError as e:
        err.write(f"Error: {e}\n")
        return 1

    target_keys = args.keys if args.keys else [
        k for k in env if is_sensitive_key(k)
    ]

    if not target_keys:
        out.write("No sensitive keys found to rotate.\n")
        return 0

    plan = rotate_env(env, target_keys, length=args.length)

    if args.dry_run:
        out.write("Dry run — keys that would be rotated:\n")
        for key in plan.rotated_keys:
            out.write(f"  ~ {key}\n")
        return 0

    if args.backup:
        from envoy.cli_backup import run_backup as _backup
        import types
        bargs = types.SimpleNamespace(file=args.file, output_dir=".env_backups", mask=False, keep=10)
        _backup(bargs, out=out, err=err)

    save_local(args.file, plan.new_env, overwrite=True)
    out.write(f"Rotated {len(plan.rotated_keys)} key(s) in {args.file}:\n")
    for key in plan.rotated_keys:
        out.write(f"  ~ {key}\n")
    return 0
