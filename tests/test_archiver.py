"""Unit tests for envoy.archiver."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from envoy.archiver import (
    ArchiveError,
    archive_env_files,
    extract_env_archive,
    list_archive_contents,
)


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    a = tmp_path / "app.env"
    b = tmp_path / "db.env"
    a.write_text("APP_NAME=myapp\nAPP_ENV=production\n")
    b.write_text("DB_HOST=localhost\nDB_PASSWORD=secret123\n")
    return tmp_path


def test_archive_creates_zip(env_dir: Path, tmp_path: Path) -> None:
    out = tmp_path / "bundle.zip"
    files = [env_dir / "app.env", env_dir / "db.env"]
    entries = archive_env_files(files, out)
    assert out.exists()
    assert set(entries) == {"app.env", "db.env"}


def test_archive_includes_manifest(env_dir: Path, tmp_path: Path) -> None:
    out = tmp_path / "bundle.zip"
    archive_env_files([env_dir / "app.env"], out, include_manifest=True)
    with zipfile.ZipFile(out) as zf:
        assert "manifest.json" in zf.namelist()


def test_archive_excludes_manifest_when_flag_off(env_dir: Path, tmp_path: Path) -> None:
    out = tmp_path / "bundle.zip"
    archive_env_files([env_dir / "app.env"], out, include_manifest=False)
    with zipfile.ZipFile(out) as zf:
        assert "manifest.json" not in zf.namelist()


def test_archive_mask_hides_sensitive_values(env_dir: Path, tmp_path: Path) -> None:
    out = tmp_path / "bundle.zip"
    archive_env_files([env_dir / "db.env"], out, mask=True, include_manifest=False)
    with zipfile.ZipFile(out) as zf:
        content = zf.read("db.env").decode()
    assert "secret123" not in content
    assert "DB_PASSWORD" in content


def test_archive_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ArchiveError, match="not found"):
        archive_env_files([tmp_path / "ghost.env"], tmp_path / "out.zip")


def test_archive_empty_list_raises(tmp_path: Path) -> None:
    with pytest.raises(ArchiveError, match="No files"):
        archive_env_files([], tmp_path / "out.zip")


def test_extract_restores_files(env_dir: Path, tmp_path: Path) -> None:
    out = tmp_path / "bundle.zip"
    archive_env_files([env_dir / "app.env", env_dir / "db.env"], out, include_manifest=False)
    dest = tmp_path / "extracted"
    extracted = extract_env_archive(out, dest)
    assert len(extracted) == 2
    names = {p.name for p in extracted}
    assert names == {"app.env", "db.env"}


def test_extract_missing_archive_raises(tmp_path: Path) -> None:
    with pytest.raises(ArchiveError, match="not found"):
        extract_env_archive(tmp_path / "ghost.zip", tmp_path / "out")


def test_list_archive_contents(env_dir: Path, tmp_path: Path) -> None:
    out = tmp_path / "bundle.zip"
    archive_env_files([env_dir / "app.env", env_dir / "db.env"], out)
    contents = list_archive_contents(out)
    assert set(contents) == {"app.env", "db.env"}


def test_list_missing_archive_raises(tmp_path: Path) -> None:
    with pytest.raises(ArchiveError, match="not found"):
        list_archive_contents(tmp_path / "nope.zip")
