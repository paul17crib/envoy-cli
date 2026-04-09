"""cli_convert.py — Convert .env files between supported formats."""

import argparse
import sys
from pathlib import Path

from envoy.parser import parse_env_file
from envoy.cli_export import format_bash, format_docker, format_yaml
import json

SUPPORTED_FORMATS = ["env", "bash", "docker", "yaml", "json"]


def build_parser(subparsers=None):
    description = "Convert a .env file to another format."
    if subparsers:
        parser = subparsers.add_parser("convert", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envoy convert", description=description)

    parser.add_argument("source", help="Source .env file path")
    parser.add_argument(
        "--from",
        dest="from_format",
        default="env",
        choices=SUPPORTED_FORMATS,
        help="Input format (default: env)",
    )
    parser.add_argument(
        "--to",
        dest="to_format",
        required=True,
        choices=SUPPORTED_FORMATS,
        help="Output format",
    )
    parser.add_argument("-o", "--output", help="Output file path (default: stdout)")
    return parser


def convert_env(env: dict, to_format: str) -> str:
    if to_format == "env":
        from envoy.parser import serialize_env
        return serialize_env(env)
    elif to_format == "bash":
        return format_bash(env)
    elif to_format == "docker":
        return format_docker(env)
    elif to_format == "yaml":
        return format_yaml(env)
    elif to_format == "json":
        return json.dumps(env, indent=2)
    else:
        raise ValueError(f"Unsupported format: {to_format}")


def run_convert(args) -> int:
    source_path = Path(args.source)
    if not source_path.exists():
        print(f"[error] Source file not found: {source_path}", file=sys.stderr)
        return 1

    try:
        env = parse_env_file(str(source_path))
    except Exception as exc:
        print(f"[error] Failed to parse source file: {exc}", file=sys.stderr)
        return 1

    try:
        output = convert_env(env, args.to_format)
    except ValueError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(output)
        print(f"[ok] Converted to {args.to_format} → {out_path}")
    else:
        print(output)

    return 0
