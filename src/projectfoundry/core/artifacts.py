"""Atomic storage helpers for large block output artifacts."""

from __future__ import annotations

import hashlib
import shutil
import tempfile
import uuid
import zipfile
from collections.abc import Callable
from pathlib import Path


class ArtifactStore:
    """Store block artifacts outside the serialized project document."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def path_for(self, relative_path: str | Path) -> Path:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def write_atomic(self, relative_path: str | Path, writer: Callable[[Path], None]) -> str:
        destination = self.path_for(relative_path)
        temporary = destination.with_name(
            f".{destination.stem}.{uuid.uuid4().hex}.tmp{destination.suffix}"
        )
        try:
            writer(temporary)
            temporary.replace(destination)
            return self.checksum(destination)
        finally:
            temporary.unlink(missing_ok=True)

    @staticmethod
    def checksum(path: str | Path) -> str:
        digest = hashlib.sha256()
        with Path(path).open("rb") as artifact:
            for chunk in iter(lambda: artifact.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def load(self, relative_path: str | Path, loader: Callable[[Path], object]) -> object:
        path = self.root / relative_path
        if not path.is_file():
            raise FileNotFoundError(f"Artifact does not exist: {relative_path}")
        return loader(path)


class ZipArtifactStore(ArtifactStore):
    """Read artifacts from a project archive, extracting only requested files."""

    def __init__(self, archive_path: str | Path) -> None:
        self.archive_path = Path(archive_path)
        self.root = Path(tempfile.mkdtemp(prefix="projectfoundry-artifacts-"))
        self._written: dict[str, Path] = {}

    def path_for(self, relative_path: str | Path) -> Path:
        relative = str(relative_path).replace("\\", "/")
        path = self.root / Path(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def write_atomic(self, relative_path: str | Path, writer: Callable[[Path], None]) -> str:
        relative = str(relative_path).replace("\\", "/")
        destination = self.path_for(relative)
        temporary = destination.with_name(
            f".{destination.stem}.{uuid.uuid4().hex}.tmp{destination.suffix}"
        )
        try:
            writer(temporary)
            temporary.replace(destination)
            self._written[relative] = destination
            return self.checksum(destination)
        finally:
            temporary.unlink(missing_ok=True)

    def load(self, relative_path: str | Path, loader: Callable[[Path], object]) -> object:
        relative = str(relative_path).replace("\\", "/")
        path = self.path_for(relative)
        if not path.is_file():
            try:
                with zipfile.ZipFile(self.archive_path) as archive:
                    path.write_bytes(archive.read(relative))
            except KeyError as error:
                raise FileNotFoundError(f"Artifact does not exist: {relative_path}") from error
        return loader(path)

    def close(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)