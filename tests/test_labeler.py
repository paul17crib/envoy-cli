"""Tests for envoy.labeler"""

import pytest
from envoy.labeler import (
    LabelError,
    build_label_comment,
    extract_labels,
    filter_by_label,
    list_all_labels,
    parse_labels_from_comment,
    remove_labels,
    set_labels,
)


def test_parse_labels_from_comment_valid():
    result = parse_labels_from_comment("# @labels: infra, prod")
    assert result == ["infra", "prod"]


def test_parse_labels_from_comment_single():
    result = parse_labels_from_comment("# @labels: dev")
    assert result == ["dev"]


def test_parse_labels_from_comment_invalid_prefix():
    result = parse_labels_from_comment("# not a label comment")
    assert result == []


def test_build_label_comment_sorts_labels():
    comment = build_label_comment(["prod", "infra", "dev"])
    assert comment == "# @labels: dev, infra, prod"


def test_build_label_comment_deduplicates():
    comment = build_label_comment(["prod", "prod", "dev"])
    assert "prod" in comment
    assert comment.count("prod") == 1


def test_extract_labels_returns_mapping():
    env = {
        "DB_HOST": "localhost",
        "__labels__DB_HOST": "# @labels: infra, prod",
        "APP_NAME": "myapp",
    }
    result = extract_labels(env)
    assert result["DB_HOST"] == ["infra", "prod"]
    assert "APP_NAME" not in result


def test_set_labels_adds_metadata_key():
    env = {"DB_HOST": "localhost"}
    updated = set_labels(env, "DB_HOST", ["infra"])
    assert "__labels__DB_HOST" in updated


def test_set_labels_does_not_mutate_original():
    env = {"DB_HOST": "localhost"}
    set_labels(env, "DB_HOST", ["infra"])
    assert "__labels__DB_HOST" not in env


def test_set_labels_missing_key_raises():
    env = {"APP_NAME": "test"}
    with pytest.raises(LabelError):
        set_labels(env, "MISSING_KEY", ["tag"])


def test_set_labels_empty_list_removes_metadata():
    env = {
        "DB_HOST": "localhost",
        "__labels__DB_HOST": "# @labels: infra",
    }
    updated = set_labels(env, "DB_HOST", [])
    assert "__labels__DB_HOST" not in updated


def test_remove_labels_clears_metadata():
    env = {
        "DB_HOST": "localhost",
        "__labels__DB_HOST": "# @labels: infra",
    }
    updated = remove_labels(env, "DB_HOST")
    assert "__labels__DB_HOST" not in updated


def test_remove_labels_no_existing_labels_is_safe():
    env = {"APP_NAME": "myapp"}
    updated = remove_labels(env, "APP_NAME")
    assert updated == env


def test_filter_by_label_returns_matching_keys():
    env = {
        "DB_HOST": "localhost",
        "__labels__DB_HOST": "# @labels: infra",
        "APP_NAME": "myapp",
        "__labels__APP_NAME": "# @labels: app",
    }
    result = filter_by_label(env, "infra")
    assert "DB_HOST" in result
    assert "APP_NAME" not in result


def test_filter_by_label_case_insensitive_default():
    env = {
        "DB_HOST": "localhost",
        "__labels__DB_HOST": "# @labels: Infra",
    }
    result = filter_by_label(env, "infra")
    assert "DB_HOST" in result


def test_filter_by_label_excludes_metadata_keys():
    env = {
        "DB_HOST": "localhost",
        "__labels__DB_HOST": "# @labels: infra",
    }
    result = filter_by_label(env, "infra")
    assert all(not k.startswith("__labels__") for k in result)


def test_list_all_labels_returns_sorted_unique():
    env = {
        "DB_HOST": "localhost",
        "__labels__DB_HOST": "# @labels: infra, prod",
        "APP_NAME": "myapp",
        "__labels__APP_NAME": "# @labels: app, prod",
    }
    labels = list_all_labels(env)
    assert labels == ["app", "infra", "prod"]


def test_list_all_labels_empty_env_returns_empty():
    assert list_all_labels({}) == []
