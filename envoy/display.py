"""Display helpers for rendering env variables in the CLI."""

from typing import Dict, Optional
from envoy.masker import mask_env, get_masked_keys, MASK_VALUE


def format_env_table(
    env: Dict[str, str],
    mask_secrets: bool = True,
    patterns: Optional[list] = None,
) -> str:
    """Format an env dict as a human-readable table string."""
    if not env:
        return "(no variables)"

    display_env = mask_env(env, patterns) if mask_secrets else dict(env)
    masked_keys = get_masked_keys(env, patterns) if mask_secrets else set()

    key_width = max(len(k) for k in display_env) + 2
    val_width = max(len(v) for v in display_env.values()) + 2

    separator = f"+{'-' * key_width}+{'-' * val_width}+"
    header = f"| {'KEY'.ljust(key_width - 2)} | {'VALUE'.ljust(val_width - 2)} |"

    lines = [separator, header, separator]
    for key in sorted(display_env):
        value = display_env[key]
        indicator = " [masked]" if key in masked_keys else ""
        val_display = f"{value}{indicator}"
        lines.append(f"| {key.ljust(key_width - 2)} | {val_display.ljust(val_width - 2)} |")
    lines.append(separator)

    return "\n".join(lines)


def summarize_env(env: Dict[str, str], mask_secrets: bool = True) -> str:
    """Return a short summary line about the env dict."""
    total = len(env)
    masked_count = len(get_masked_keys(env)) if mask_secrets else 0
    visible_count = total - masked_count
    return (
        f"{total} variable(s) total: "
        f"{visible_count} visible, {masked_count} masked."
    )
