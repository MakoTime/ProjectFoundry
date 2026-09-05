"""Factory for the project launcher window."""

from __future__ import annotations

from pathlib import Path

from ..package import ProjectPackage
from ..recent import RecentProjectStore
from .model import ProjectLauncherModel
from .view import ProjectLauncherView


class ProjectLauncherFactory:
    """Build a launcher with configurable package and recent-project storage."""

    @staticmethod
    def create(
        *,
        extension: str = ".pfzip",
        recent_path: str | Path | None = None,
        serializer=None,
        parent=None,
    ) -> ProjectLauncherView:
        package = ProjectPackage(extension)
        recent_store = RecentProjectStore(recent_path) if recent_path is not None else None
        model = ProjectLauncherModel(package, recent_store, serializer)
        return ProjectLauncherView(model, parent)
