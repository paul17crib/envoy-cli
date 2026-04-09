from dataclasses import dataclass
from typing import Dict, List, Set
from envoy.masker import is_sensitive_key


@dataclass
class AuditResult:
    key: str
    level: str  # "error", "warning", "info"
    message: str


_PLACEHOLDER_PATTERNS = ("changeme", "replace_me", "todo", "fixme", "xxx", "your_", "<", ">")


def _looks_like_placeholder(value: str) -> bool:
    lower = value.lower()
    return any(p in lower for p in _PLACEHOLDER_PATTERNS)


def audit_env(env: Dict[str, str]) -> List[AuditResult]:
    results: List[AuditResult] = []

    for key, value in env.items():
        if is_sensitive_key(key):
            if not value:
                results.append(AuditResult(
                    key=key,
                    level="error",
                    message="Sensitive key has an empty value.",
                ))
            elif _looks_like_placeholder(value):
                results.append(AuditResult(
                    key=key,
                    level="warning",
                    message=f"Sensitive key appears to contain a placeholder value.",
                ))
            elif len(value) < 8:
                results.append(AuditResult(
                    key=key,
                    level="warning",
                    message="Sensitive key value is very short (< 8 chars); may be weak.",
                ))
        else:
            if not value:
                results.append(AuditResult(
                    key=key,
                    level="info",
                    message="Key has an empty value.",
                ))

    return results


def format_audit_report(results: List[AuditResult], masked_keys: Set[str]) -> str:
    if not results:
        return "✔ No audit issues found."

    lines = [f"Audit found {len(results)} issue(s):\n"]
    icons = {"error": "✖", "warning": "⚠", "info": "ℹ"}

    for r in results:
        icon = icons.get(r.level, "?")
        display_key = f"{r.key} (masked)" if r.key in masked_keys else r.key
        lines.append(f"  {icon} [{r.level.upper()}] {display_key}: {r.message}")

    return "\n".join(lines)
