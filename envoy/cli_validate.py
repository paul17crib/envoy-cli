"""CLI entry point for the `envoy validate` sub-command."""

import sys
from typing import List, Optional

from envoy.sync import load_local, SyncError
from envoy.validator import validate_env, has_errors, format_issues


def run_validate(
    env_path: str = '.env',
    required_keys: Optional[List[str]] = None,
    strict: bool = False,
) -> int:
    """Validate a local .env file.

    Parameters
    ----------
    env_path:
        Path to the .env file to validate.
    required_keys:
        Optional list of keys that must be present.
    strict:
        If True, treat warnings as errors (non-zero exit).

    Returns
    -------
    int
        Exit code: 0 for success, 1 for validation failures.
    """
    try:
        env = load_local(env_path)
    except SyncError as exc:
        print(f'[envoy] Error loading file: {exc}', file=sys.stderr)
        return 1

    issues = validate_env(env, required_keys=required_keys or [])

    if not issues:
        print(f'[envoy] {env_path} is valid. ({len(env)} keys checked)')
        return 0

    print(f'[envoy] Validation issues in {env_path}:')
    print(format_issues(issues))

    if strict:
        return 1 if issues else 0

    return 1 if has_errors(issues) else 0


if __name__ == '__main__':  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(description='Validate a .env file')
    parser.add_argument('file', nargs='?', default='.env', help='Path to .env file')
    parser.add_argument(
        '--require', nargs='*', metavar='KEY', help='Keys that must be present'
    )
    parser.add_argument(
        '--strict', action='store_true', help='Treat warnings as failures'
    )
    args = parser.parse_args()
    sys.exit(run_validate(args.file, required_keys=args.require, strict=args.strict))
