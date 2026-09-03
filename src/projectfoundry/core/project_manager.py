"""Application-scoped manager for the active project."""

from __future__ import annotations

from collections.abc import Callable

from .project import Project


class ProjectManager:
    """Provide one active project without making Project itself a singleton."""

    _instance: ProjectManager | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._project = Project()
        self._callbacks: list[Callable[[Project], None]] = []

    @property
    def current_project(self) -> Project:
        return self._project

    def add_project_changed_callback(self, callback: Callable[[Project], None]) -> None:
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def set_current_project(self, project: Project) -> Project:
        if project is self._project:
            return project
        previous = self._project
        self._project = project
        previous.shutdown()
        for callback in tuple(self._callbacks):
            callback(project)
        return project

    def new_project(self) -> Project:
        return self.set_current_project(Project())

    def reset(self) -> Project:
        return self.new_project()

    @classmethod
    def reset_singleton(cls) -> None:
        if cls._instance is not None:
            cls._instance._project.shutdown()
        cls._instance = None