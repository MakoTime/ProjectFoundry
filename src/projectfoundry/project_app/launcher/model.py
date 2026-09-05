"""Framework-neutral project launcher state and workflows."""

from __future__ import annotations

from pathlib import Path

from ..package import ProjectContext, ProjectPackage
from ..recent import RecentProject, RecentProjectStore


class ProjectLauncherModel:
    """Coordinate project package workflows without depending on Qt."""

    def __init__(
        self,
        package: ProjectPackage | None = None,
        recent_store: RecentProjectStore | None = None,
        serializer=None,
    ) -> None:
        self.package = package or ProjectPackage()
        self.recent_store = recent_store
        self.serializer = serializer

    def recent_projects(self) -> list[RecentProject]:
        return self.recent_store.list() if self.recent_store is not None else []

    def create_project(self, path: str | Path, name: str = "Untitled Project") -> ProjectContext:
        package_path = self.package.create(path, name=name)
        context = self.package.open_context(package_path, serializer=self.serializer)
        self._remember(name, package_path)
        return context

    def open_recent(self, project: RecentProject) -> ProjectContext:
        context = self.package.open_context(project.path, serializer=self.serializer)
        self._remember(project.name, project.path, project.format)
        return context

    def open_file(self, path: str | Path) -> ProjectContext:
        project_path = Path(path)
        context = self.package.open_context(project_path, serializer=self.serializer)
        self._remember(project_path.stem, project_path)
        return context

    def _remember(self, name: str, path: str | Path, format: str = "projectfoundry") -> None:
        if self.recent_store is not None:
            self.recent_store.add(name, path, format)

    def save_project(self, context: ProjectContext) -> None:
        if self.serializer is None:
            raise RuntimeError("Project launcher requires a serializer to save projects")
        context.save(self.package, self.serializer)
