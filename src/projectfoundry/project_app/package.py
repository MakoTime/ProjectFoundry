"""Durable project package and working-context services."""

from __future__ import annotations

import json
import shutil
import tempfile
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path

from ..core import ArtifactStore, Project, ZipArtifactStore


@dataclass
class ProjectContext:
    """An opened project and the directory containing its live files."""

    package_path: Path
    working_directory: Path | None
    project: Project

    def __post_init__(self) -> None:
        self.dirty = False
        self._closed = False
        self.project.add_event_callback(self._project_changed)

    def _project_changed(self, event) -> None:
        if event.kind not in {"block_added", "object_added"}:
            self.dirty = True

    @property
    def artifact_store(self) -> ArtifactStore:
        return self.project.artifact_store

    def save(self, package: "ProjectPackage", serializer) -> None:
        """Save project state to the working directory and repack it."""
        if self.working_directory is not None:
            serializer.save_project(self.project, self.working_directory / package.project_document)
            package.pack(self.working_directory, self.package_path)
        else:
            package.save_archive(
                self.package_path,
                serializer.project_document(self.project),
                self.project.artifact_store,
            )
        self.dirty = False

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self.project.remove_event_callback(self._project_changed)
        close = getattr(self.project.artifact_store, "close", None)
        if close is not None:
            close()
        self.project.shutdown()


class ProjectPackage:
    """Create, extract, and atomically update ZIP-based project packages."""

    project_document = "project.json"
    metadata_document = "metadata.json"

    def __init__(self, extension: str = ".pfzip") -> None:
        self.extension = extension if extension.startswith(".") else f".{extension}"

    def create(self, path: str | Path, *, name: str = "Untitled Project") -> Path:
        package_path = Path(path)
        package_path.parent.mkdir(parents=True, exist_ok=True)
        if package_path.suffix != self.extension:
            package_path = package_path.with_suffix(self.extension)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / self.project_document).write_text(
                json.dumps(
                    {"version": "1.0.0", "blocks": [], "tree": [], "scene_table": []},
                    indent=2,
                ),
                encoding="utf-8",
            )
            (root / self.metadata_document).write_text(
                json.dumps({"name": name, "format": "projectfoundry"}, indent=2),
                encoding="utf-8",
            )
            self._replace_from_directory(root, package_path)
        return package_path

    def extract(
        self,
        package_path: str | Path,
        working_root: str | Path | None = None,
    ) -> Path:
        package_path = Path(package_path)
        if not package_path.is_file():
            raise FileNotFoundError(package_path)
        if not zipfile.is_zipfile(package_path):
            raise ValueError(f"Not a project package: {package_path}")
        root = Path(working_root) if working_root is not None else package_path.parent
        working_directory = root / package_path.stem
        if working_directory.exists():
            shutil.rmtree(working_directory)
        working_directory.mkdir(parents=True, exist_ok=False)
        try:
            with zipfile.ZipFile(package_path) as archive:
                self._validate_members(archive)
                archive.extractall(working_directory)
            if not (working_directory / self.project_document).is_file():
                raise ValueError("Project package has no project.json")
        except Exception:
            shutil.rmtree(working_directory, ignore_errors=True)
            raise
        return working_directory

    def pack(self, working_directory: str | Path, package_path: str | Path) -> Path:
        destination = Path(package_path)
        if destination.suffix != self.extension:
            destination = destination.with_suffix(self.extension)
        self._replace_from_directory(Path(working_directory), destination)
        return destination

    def open_context(
        self,
        package_path: str | Path,
        *,
        working_root: str | Path | None = None,
        project: Project | None = None,
        serializer=None,
    ) -> ProjectContext:
        package_path = Path(package_path)
        if working_root is not None:
            working_directory = self.extract(package_path, working_root)
            active_project = project or Project(ArtifactStore(working_directory / "artifacts"))
        else:
            working_directory = None
            active_project = project or Project(ZipArtifactStore(package_path))
        if serializer is not None:
            with zipfile.ZipFile(package_path) as archive:
                document = json.loads(archive.read(self.project_document))
            serializer.load_document(document, active_project)
        return ProjectContext(package_path, working_directory, active_project)

    def save_archive(
        self,
        package_path: str | Path,
        document: dict,
        artifact_store: ArtifactStore | None = None,
    ) -> Path:
        """Atomically rewrite a package without extracting the whole project."""
        package_path = Path(package_path)
        temporary = package_path.with_name(f".{package_path.name}.{uuid.uuid4().hex}.tmp")
        replacements = getattr(artifact_store, "_written", {}) if artifact_store else {}
        try:
            with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as output:
                if package_path.is_file() and zipfile.is_zipfile(package_path):
                    with zipfile.ZipFile(package_path) as source:
                        for member in source.infolist():
                            if member.filename not in {self.project_document, *replacements}:
                                output.writestr(member, source.read(member.filename))
                output.writestr(
                    self.project_document,
                    json.dumps(document, indent=2).encode("utf-8"),
                )
                for relative, path in replacements.items():
                    output.write(path, relative)
            temporary.replace(package_path)
        finally:
            temporary.unlink(missing_ok=True)
        return package_path

    @staticmethod
    def _validate_members(archive: zipfile.ZipFile) -> None:
        for member in archive.infolist():
            member_path = Path(member.filename)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise ValueError(f"Unsafe project package member: {member.filename}")

    @classmethod
    def _replace_from_directory(cls, source: Path, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.tmp")
        try:
            with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
                for path in source.rglob("*"):
                    if path.is_file():
                        archive.write(path, path.relative_to(source).as_posix())
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)