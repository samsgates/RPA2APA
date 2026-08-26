from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path


class UnsafeArchive(ValueError):
    pass


def extract_project_zip(source_file: str | Path, workspace_root: str | Path | None = None) -> Path:
    """Safely extract a user-supplied UiPath ZIP into an isolated workspace."""
    source_file = Path(source_file)
    root = Path(workspace_root) if workspace_root else Path(tempfile.mkdtemp(prefix="rpa2apa-upload-"))
    root.mkdir(parents=True, exist_ok=True)
    destination = root / "project"
    destination.mkdir(exist_ok=True)

    with zipfile.ZipFile(source_file) as zf:
        for info in zf.infolist():
            member = Path(info.filename)
            if member.is_absolute() or ".." in member.parts:
                raise UnsafeArchive(f"Unsafe archive member: {info.filename}")
            resolved = (destination / member).resolve()
            if destination.resolve() not in resolved.parents and resolved != destination.resolve():
                raise UnsafeArchive(f"Archive escapes workspace: {info.filename}")
        zf.extractall(destination)

    # Common GitHub/export archives contain one top-level folder.
    children = [p for p in destination.iterdir() if not p.name.startswith(".")]
    if len(children) == 1 and children[0].is_dir() and not (destination / "project.json").exists():
        return children[0]
    return destination
