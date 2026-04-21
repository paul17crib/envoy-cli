"""Unit tests for envoy.sharer."""

import time

import pytest

from envoy.sharer import ShareError, create_share, list_shares, load_share, revoke_share


@pytest.fixture
def base(tmp_path):
    return tmp_path


@pytest.fixture
def sample_env():
    return {"APP_KEY": "abc123", "SECRET_TOKEN": "supersecret", "DEBUG": "true"}


def test_create_share_returns_token(base, sample_env):
    token = create_share(sample_env, label="test", base=base)
    assert isinstance(token, str)
    assert len(token) == 12


def test_create_share_masks_sensitive_by_default(base, sample_env):
    token = create_share(sample_env, label="masked", base=base)
    env = load_share(token, base=base)
    assert env["SECRET_TOKEN"] == "***"
    assert env["APP_KEY"] == "abc123"


def test_create_share_no_mask_preserves_values(base, sample_env):
    token = create_share(sample_env, label="plain", mask=False, base=base)
    env = load_share(token, base=base)
    assert env["SECRET_TOKEN"] == "supersecret"


def test_load_share_missing_token_raises(base):
    with pytest.raises(ShareError, match="not found"):
        load_share("nonexistent", base=base)


def test_load_share_expired_raises(base, sample_env):
    token = create_share(sample_env, label="short", ttl_seconds=1, base=base)
    time.sleep(1.1)
    with pytest.raises(ShareError, match="expired"):
        load_share(token, base=base)


def test_create_share_empty_label_raises(base, sample_env):
    with pytest.raises(ShareError, match="label"):
        create_share(sample_env, label="", base=base)


def test_create_share_zero_ttl_raises(base, sample_env):
    with pytest.raises(ShareError, match="ttl"):
        create_share(sample_env, label="bad", ttl_seconds=0, base=base)


def test_list_shares_returns_all(base, sample_env):
    create_share(sample_env, label="first", base=base)
    create_share(sample_env, label="second", base=base)
    shares = list_shares(base=base)
    assert len(shares) == 2
    labels = {s["label"] for s in shares}
    assert labels == {"first", "second"}


def test_list_shares_marks_expired(base, sample_env):
    create_share(sample_env, label="live", ttl_seconds=3600, base=base)
    create_share(sample_env, label="dead", ttl_seconds=1, base=base)
    time.sleep(1.1)
    shares = list_shares(base=base)
    expired = [s for s in shares if s["expired"]]
    active = [s for s in shares if not s["expired"]]
    assert len(expired) == 1
    assert len(active) == 1


def test_revoke_share_removes_file(base, sample_env):
    token = create_share(sample_env, label="temp", base=base)
    assert revoke_share(token, base=base) is True
    with pytest.raises(ShareError):
        load_share(token, base=base)


def test_revoke_nonexistent_returns_false(base):
    assert revoke_share("doesnotexist", base=base) is False


def test_list_shares_empty_dir(base):
    assert list_shares(base=base) == []
