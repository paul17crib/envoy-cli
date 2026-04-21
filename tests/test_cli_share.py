"""Tests for envoy.cli_share."""

import time

import pytest

from envoy.cli_share import build_parser, run_share
from envoy.sharer import create_share


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("APP_KEY=hello\nSECRET_TOKEN=topsecret\nDEBUG=true\n")
    return p


@pytest.fixture
def share_dir(tmp_path):
    return tmp_path / "shares"


def make_args(action, **kwargs):
    p = build_parser()
    base = [action]
    for k, v in kwargs.items():
        flag = k.replace("_", "-")
        if isinstance(v, bool):
            if v:
                base.append(f"--{flag}")
        else:
            base += [f"--{flag}", str(v)]
    return p.parse_args(base)


def test_build_parser_returns_parser():
    p = build_parser()
    assert p is not None


def test_create_share_writes_token(env_file, share_dir, capsys):
    args = build_parser().parse_args(
        ["create", str(env_file), "--label", "ci", "--share-dir", str(share_dir)]
    )
    rc = run_share(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Token:" in out


def test_create_share_missing_file_returns_error(tmp_path, share_dir, capsys):
    args = build_parser().parse_args(
        ["create", str(tmp_path / "missing.env"), "--label", "x", "--share-dir", str(share_dir)]
    )
    rc = run_share(args)
    assert rc == 1
    assert "not found" in capsys.readouterr().err


def test_list_shares_empty(share_dir, capsys):
    args = build_parser().parse_args(["list", "--share-dir", str(share_dir)])
    rc = run_share(args)
    assert rc == 0
    assert "No shares" in capsys.readouterr().out


def test_list_shares_shows_entries(env_file, share_dir, capsys):
    create_args = build_parser().parse_args(
        ["create", str(env_file), "--label", "myshare", "--share-dir", str(share_dir)]
    )
    run_share(create_args)
    list_args = build_parser().parse_args(["list", "--share-dir", str(share_dir)])
    rc = run_share(list_args)
    assert rc == 0
    assert "myshare" in capsys.readouterr().out


def test_get_share_prints_env(env_file, share_dir, capsys):
    create_args = build_parser().parse_args(
        ["create", str(env_file), "--label", "get-test", "--no-mask", "--share-dir", str(share_dir)]
    )
    run_share(create_args)
    token = capsys.readouterr().out.split("Token:")[-1].strip()
    get_args = build_parser().parse_args(["get", token, "--share-dir", str(share_dir)])
    rc = run_share(get_args)
    assert rc == 0
    assert "APP_KEY=hello" in capsys.readouterr().out


def test_get_missing_token_returns_error(share_dir, capsys):
    args = build_parser().parse_args(["get", "badtoken", "--share-dir", str(share_dir)])
    rc = run_share(args)
    assert rc == 1
    assert "not found" in capsys.readouterr().err


def test_revoke_share_succeeds(env_file, share_dir, capsys):
    create_args = build_parser().parse_args(
        ["create", str(env_file), "--label", "rev", "--share-dir", str(share_dir)]
    )
    run_share(create_args)
    token = capsys.readouterr().out.split("Token:")[-1].strip()
    rev_args = build_parser().parse_args(["revoke", token, "--share-dir", str(share_dir)])
    rc = run_share(rev_args)
    assert rc == 0
    assert "Revoked" in capsys.readouterr().out


def test_revoke_missing_token_returns_error(share_dir, capsys):
    args = build_parser().parse_args(["revoke", "ghost", "--share-dir", str(share_dir)])
    rc = run_share(args)
    assert rc == 1
