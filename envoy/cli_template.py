import argparse
import os
import re
from envoy.parser import parse_env_file, serialize_env
from envoy.sync import SyncError


def build_parser(subparsers=None):
    description = "Render a template file by substituting .env variables."
    if subparsers:
        parser = subparsers.add_parser("template", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envoy template", description=description)

    parser.add_argument("template", help="Path to the template file (uses {{KEY}} placeholders)")
    parser.add_argument(
        "--env", default=".env", metavar="FILE", help="Path to .env file (default: .env)"
    )
    parser.add_argument(
        "--output", "-o", default=None, metavar="FILE",
        help="Write rendered output to this file (default: stdout)"
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="Fail if any template placeholder has no matching key"
    )
    return parser


def render_template(template_text: str, env: dict, strict: bool = False) -> tuple[str, list[str]]:
    """Substitute {{KEY}} placeholders with values from env dict.

    Returns (rendered_text, list_of_missing_keys).
    """
    missing = []
    pattern = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")

    def replacer(match):
        key = match.group(1)
        if key in env:
            return env[key]
        missing.append(key)
        return match.group(0)  # leave placeholder intact if missing

    rendered = pattern.sub(replacer, template_text)
    return rendered, missing


def run_template(args) -> int:
    # Load env
    try:
        env = parse_env_file(args.env)
    except FileNotFoundError:
        print(f"[error] .env file not found: {args.env}")
        return 1
    except SyncError as e:
        print(f"[error] {e}")
        return 1

    # Load template
    try:
        with open(args.template, "r") as f:
            template_text = f.read()
    except FileNotFoundError:
        print(f"[error] Template file not found: {args.template}")
        return 1

    rendered, missing = render_template(template_text, env, strict=args.strict)

    if missing:
        for key in missing:
            print(f"[warn] No value found for placeholder: {{{{{key}}}}}")
        if args.strict:
            print(f"[error] Strict mode: {len(missing)} unresolved placeholder(s).")
            return 1

    if args.output:
        with open(args.output, "w") as f:
            f.write(rendered)
        print(f"[ok] Rendered template written to {args.output}")
    else:
        print(rendered, end="")

    return 0
