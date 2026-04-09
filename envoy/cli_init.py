"""CLI command for initializing a new .env file from a template."""

import argparse
import os
from typing import Optional

from envoy.parser import serialize_env
from envoy.validator import validate_env, has_errors, format_issues


DEFAULT_TEMPLATE: dict[str, str] = {
    "APP_NAME": "",
    "APP_ENV": "development",
    "APP_PORT": "8000",
    "SECRET_KEY": "",
    "DATABASE_URL": "",
    "DEBUG": "false",
}


def build_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Initialize a new .env file from a default template."
    if subparsers is not None:
        parser = subparsers.add_parser("init", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envoy init", description=description)

    parser.add_argument(
        "--output",
        "-o",
        default=".env",
        help="Path to write the new .env file (default: .env)",
    )
    parser.add_argument(
        "--template",
        "-t",
        default=None,
        help="Path to an existing .env file to use as a template.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite the output file if it already exists.",
    )
    return parser


def run_init(args, out=None) -> int:
    import sys
    if out is None:
        out = sys.stdout

    output_path: str = args.output
    template_path: Optional[str] = args.template
    overwrite: bool = args.overwrite

    if os.path.exists(output_path) and not overwrite:
        out.write(
            f"[error] '{output_path}' already exists. Use --overwrite to replace it.\n"
        )
        return 1

    if template_path is not None:
        if not os.path.exists(template_path):
            out.write(f"[error] Template file '{template_path}' not found.\n")
            return 1
        from envoy.parser import parse_env_file
        env: dict[str, str] = parse_env_file(template_path)
        # Strip values so the template becomes a blank scaffold
        env = {k: "" for k in env}
    else:
        env = dict(DEFAULT_TEMPLATE)

    issues = validate_env(env)
    if has_errors(issues):
        out.write("[warning] Template contains validation errors:\n")
        out.write(format_issues(issues) + "\n")

    content = serialize_env(env)
    with open(output_path, "w") as f:
        f.write(content)

    out.write(f"[ok] Initialized '{output_path}' with {len(env)} key(s).\n")
    return 0
