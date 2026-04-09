import argparse
import sys
from envoy.sync import load_local, SyncError
from envoy.validator import validate_env, has_errors, format_issues
from envoy.masker import is_sensitive_key


def build_parser(subparsers=None):
    description = "Lint a .env file for common issues and best practices."
    if subparsers:
        parser = subparsers.add_parser("lint", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envoy lint", description=description)

    parser.add_argument(
        "file",
        nargs="?",
        default=".env",
        help="Path to the .env file (default: .env)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors",
    )
    parser.add_argument(
        "--check-secrets",
        action="store_true",
        help="Warn if sensitive keys have empty or placeholder values",
    )
    return parser


def run_lint(args, out=None):
    import sys
    if out is None:
        out = sys.stdout

    try:
        env = load_local(args.file)
    except SyncError as e:
        print(f"[error] {e}", file=out)
        return 1

    issues = validate_env(env)

    if args.check_secrets:
        placeholders = {"changeme", "placeholder", "secret", "example", "todo", "fixme", "xxx"}
        for key, value in env.items():
            if is_sensitive_key(key) and value.lower() in placeholders:
                from envoy.validator import ValidationIssue
                issues.append(ValidationIssue(
                    key=key,
                    message=f"Sensitive key '{key}' appears to have a placeholder value.",
                    level="warning",
                ))

    if not issues:
        print(f"[ok] No issues found in '{args.file}'.", file=out)
        return 0

    for line in format_issues(issues):
        print(line, file=out)

    error_count = sum(1 for i in issues if i.level == "error")
    warning_count = sum(1 for i in issues if i.level == "warning")
    print(f"\n{error_count} error(s), {warning_count} warning(s) in '{args.file}'.", file=out)

    if has_errors(issues):
        return 1
    if args.strict and warning_count > 0:
        return 1
    return 0
