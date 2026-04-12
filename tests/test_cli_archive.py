"""Tests for envoy.cli_archive."""

from __future__ import annotations

import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from envoy.cli_archive import run_archive


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    (tmp_path / "alpha.env").write_text("KEY_A=hello\nAPI_SECRET=topsecret\n")
    (tmp_path / "beta.env").write_text("KEY_B=world\n")
    return tmp_path


def make_create_args(env_dir: Path, output: Path, **kwargs):
    return SimpleNamespace(
        archive_cmd="create",
        files=[str(env_dir / "alpha.env"), str(env_dir / "beta.env")],
        output=str(output),
        mask=kwargs.get("mask", False),
        no_manifest=kwargs.get("no_manifest", False),
    )


def test_create_returns_zero(env_dir: Path, tmp_path: Path) -> None:
    out = tmp_path / "out.zip"
    args = make_create_args(env_dir, out)
    assert run_archive(args) == 0
    assert out.exists()


def test_create_output_contains_both_files(env_dir: Path, tmp_path: Path) -> None:
    out = tmp_path / "out.zip"
    args = make_create_args(env_dir, out)
    run_archive(args)
    with zipfile.ZipFile(out) as zf:
        names = zf.namelist()
    assert "alpha.env" in names
    assert "beta.env" in names


def test_create_mask_hides_secrets(env_dir: Path, tmp_path: Path) -> None:
    out = tmp_path / "out.zip"
    args = make_create_args(env_dir, out, mask=True, no_manifest=True)
    run_archive(args)
    with zipfile.ZipFile(out) as zf:
        content = zf.read("alpha.env").decode()
    assert "topsecret" not in content


def test_create_missing_file_returns_error(tmp_path: Path) -> None:
    args = SimpleNamespace(
        archive_cmd="create",
        files=[str(tmp_path / "ghost.env")],
        output=str(tmp_path / "out.zip"),
        mask=False,
        no_manifest=False,
    )
    assert run_archive(args) == 1


def test_extract_restores_files(env_dir: Path, tmp_path: Path) -> None:
    out = tmp_path / "out.zip"
    make_create_args(env_dir, out)
    run_archive(make_create_args(env_dir, out, no_manifest=True))
    dest = tmp_path / "dest"
    args = SimpleNamespace(archive_cmd="extract", archive=str(out), dest=str(dest))
    result = run_archive(args)
    assert result == 0
    assert (dest / "alpha.env").exists()
    assert (dest / "beta.env").exists()


def test_extract_missing_archive_returns_error(tmp_path: Path) -> None:
    args = SimpleNamespace(
        archive_cmd="extract",
        archive=str(tmp_path / "nope.zip"),
        dest=str(tmp_path / "out"),
    )
    assert run_archive(args) == 1


def test_list_shows_entries(env_dir: Path, tmp_path: Path, capsys) -> None:
    out = tmp_path / "out.zip"
    run_archive(make_create_args(env_dir, out, no_manifest=True))
    args = SimpleNamespace(archive_cmd="list", archive=str(out))
    result = run_archive(args)
    assert result == 0
    captured = capsys.readouterr()
    assert "alpha.env" in captured.out
    assert "beta.env" in captured.out


def test_list_missing_archive_returns_error(tmp_path: Path) -> None:
    args = SimpleNamespace(archive_cmd="list", archive=str(tmp_path / "nope.zip"))
    assert run_archive(args) == 1
