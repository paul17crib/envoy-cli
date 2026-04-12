"""Archive multiple .env files into a single zip bundle with optional masking."""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

from envoy.masker import mask_env
from envoy.parser import parse_env_file, serialize_env


class ArchiveError(Exception):
    """Raised when archiving or extraction fails."""


def archive_env_files(
    paths: List[Path],
    dest: Path,
    *,
    mask: bool = False,
    include_manifest: bool = True,
) -> List[str]:
    """Bundle one or more .env files into a zip archive.

    Returns a list of archived entry names.
    """
    if not paths:
        raise ArchiveError("No files provided to archive.")

    entries: List[str] = []
    manifest: Dict[str, str] = {}

    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in paths:
            if not path.exists():
                raise ArchiveError(f"File not found: {path}")

            env = parse_env_file(path)
            if mask:
                env = mask_env(env)

            content = serialize_env(env)
            entry_name = path.name
            zf.writestr(entry_name, content)
            entries.append(entry_name)
            manifest[entry_name] = str(path.resolve())

        if include_manifest:
            manifest_content = json.dumps(manifest, indent=2)
            zf.writestr("manifest.json", manifest_content)

    return entries


def extract_env_archive(src: Path, dest_dir: Path) -> List[Path]:
    """Extract all .env files from a zip archive into dest_dir.

    Returns a list of extracted file paths.
    """
    if not src.exists():
        raise ArchiveError(f"Archive not found: {src}")

    dest_dir.mkdir(parents=True, exist_ok=True)
    extracted: List[Path] = []

    with zipfile.ZipFile(src, "r") as zf:
        for name in zf.namelist():
            if name == "manifest.json":
                continue
            data = zf.read(name)
            out_path = dest_dir / name
            out_path.write_bytes(data)
            extracted.append(out_path)

    return extracted


def list_archive_contents(src: Path) -> List[str]:
    """Return the list of entry names inside an archive (excluding manifest)."""
    if not src.exists():
        raise ArchiveError(f"Archive not found: {src}")
    with zipfile.ZipFile(src, "r") as zf:
        return [n for n in zf.namelist() if n != "manifest.json"]
