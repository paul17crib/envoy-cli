"""Label management for .env keys — add, remove, list, and filter by labels."""

from __future__ import annotations

from typing import Dict, List, Optional

LABEL_COMMENT_PREFIX = "# @labels:"


class LabelError(Exception):
    pass


def parse_labels_from_comment(comment: str) -> List[str]:
    """Extract labels from a label comment line."""
    comment = comment.strip()
    if not comment.startswith(LABEL_COMMENT_PREFIX):
        return []
    raw = comment[len(LABEL_COMMENT_PREFIX):].strip()
    return [lbl.strip() for lbl in raw.split(",") if lbl.strip()]


def build_label_comment(labels: List[str]) -> str:
    """Build a label comment line from a list of labels."""
    sorted_labels = sorted(set(labels))
    return f"{LABEL_COMMENT_PREFIX} {', '.join(sorted_labels)}"


def extract_labels(env: Dict[str, str]) -> Dict[str, List[str]]:
    """Return a mapping of key -> labels by scanning inline comment metadata."""
    result: Dict[str, List[str]] = {}
    lines = list(env.items())
    for key, value in lines:
        meta_key = f"__labels__{key}"
        if meta_key in env:
            result[key] = parse_labels_from_comment(env[meta_key])
    return result


def set_labels(env: Dict[str, str], key: str, labels: List[str]) -> Dict[str, str]:
    """Attach labels to a key by storing metadata entry. Returns new dict."""
    if key not in env:
        raise LabelError(f"Key '{key}' not found in env.")
    updated = dict(env)
    meta_key = f"__labels__{key}"
    if labels:
        updated[meta_key] = build_label_comment(labels)
    else:
        updated.pop(meta_key, None)
    return updated


def remove_labels(env: Dict[str, str], key: str) -> Dict[str, str]:
    """Remove all labels from a key. Returns new dict."""
    updated = dict(env)
    updated.pop(f"__labels__{key}", None)
    return updated


def filter_by_label(
    env: Dict[str, str],
    label: str,
    case_sensitive: bool = False,
) -> Dict[str, str]:
    """Return only keys that have the given label attached."""
    label_cmp = label if case_sensitive else label.lower()
    labels_map = extract_labels(env)
    matched: Dict[str, str] = {}
    for key, value in env.items():
        if key.startswith("__labels__"):
            continue
        key_labels = labels_map.get(key, [])
        normalized = [l if case_sensitive else l.lower() for l in key_labels]
        if label_cmp in normalized:
            matched[key] = value
    return matched


def list_all_labels(env: Dict[str, str]) -> List[str]:
    """Return a sorted unique list of all labels used across all keys."""
    seen: set = set()
    labels_map = extract_labels(env)
    for labels in labels_map.values():
        seen.update(labels)
    return sorted(seen)
