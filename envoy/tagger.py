"""Tag management for .env entries — attach, remove, and filter by tags."""

from typing import Dict, List, Optional

TAG_COMMENT_PREFIX = "# @tags:"


def parse_tags_from_comment(comment: str) -> List[str]:
    """Extract tags from a tag comment line like '# @tags: prod, secret'."""
    comment = comment.strip()
    if not comment.startswith(TAG_COMMENT_PREFIX):
        return []
    raw = comment[len(TAG_COMMENT_PREFIX):].strip()
    return [t.strip() for t in raw.split(",") if t.strip()]


def build_tag_comment(tags: List[str]) -> str:
    """Serialize a list of tags into a tag comment string."""
    return f"{TAG_COMMENT_PREFIX} {', '.join(sorted(tags))}"


def extract_tags(env: Dict[str, str]) -> Dict[str, List[str]]:
    """Return a mapping of key -> tags by scanning __tags__KEY meta-entries."""
    result: Dict[str, List[str]] = {}
    prefix = "__tags__"
    for k, v in env.items():
        if k.startswith(prefix):
            real_key = k[len(prefix):]
            result[real_key] = [t.strip() for t in v.split(",") if t.strip()]
    return result


def set_tags(env: Dict[str, str], key: str, tags: List[str]) -> Dict[str, str]:
    """Attach tags to a key by storing a __tags__KEY meta-entry."""
    updated = dict(env)
    if tags:
        updated[f"__tags__{key}"] = ", ".join(sorted(tags))
    else:
        updated.pop(f"__tags__{key}", None)
    return updated


def remove_tags(env: Dict[str, str], key: str) -> Dict[str, str]:
    """Remove all tags from a key."""
    return set_tags(env, key, [])


def filter_by_tag(env: Dict[str, str], tag: str) -> Dict[str, str]:
    """Return only keys that have the given tag (excludes meta-entries)."""
    tags_map = extract_tags(env)
    return {
        k: v
        for k, v in env.items()
        if not k.startswith("__tags__") and tag in tags_map.get(k, [])
    }


def list_tags(env: Dict[str, str]) -> List[str]:
    """Return a sorted list of all unique tags used in the env."""
    tags_map = extract_tags(env)
    all_tags: set = set()
    for tags in tags_map.values():
        all_tags.update(tags)
    return sorted(all_tags)
