"""Qt launcher window for selecting a Project Foundry project."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from ..package import ProjectContext
from ..recent import RecentProject
from .model import ProjectLauncherModel


class ProjectLauncherView(QDialog):
    """Offer new, recent, and file-based project opening actions."""

    project_opened = Signal(object)

    def __init__(self, model: ProjectLauncherModel, parent=None) -> None:
        super().__init__(parent)
        self.model = model
        self.setWindowTitle("Open Project Foundry")
        self.recent_list = QListWidget(self)
        self.new_button = QPushButton("New Project", self)
        self.open_button = QPushButton("Open File", self)
        self._recent_projects: list[RecentProject] = []
        self._build_ui()
        self.refresh_recent()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Recent Projects", self))
        layout.addWidget(self.recent_list)
        buttons = QHBoxLayout()
        buttons.addWidget(self.new_button)
        buttons.addWidget(self.open_button)
        layout.addLayout(buttons)
        self.new_button.clicked.connect(self._new_project)
        self.open_button.clicked.connect(self._open_file)
        self.recent_list.itemDoubleClicked.connect(self._open_recent_item)

    def refresh_recent(self) -> None:
        self.recent_list.clear()
        self._recent_projects = self.model.recent_projects()
        for project in self._recent_projects:
            item = QListWidgetItem(f"{project.name}  |  {project.path}")
            self.recent_list.addItem(item)

    def _new_project(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Create Project",
            "",
            f"Project Foundry (*{self.model.package.extension});;All Files (*)",
        )
        if not path:
            return
        name = Path(path).stem
        context = self.model.create_project(path, name=name)
        self.project_opened.emit(context)
        self.accept()

    def _open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Project",
            "",
            f"Project Foundry (*{self.model.package.extension});;All Files (*)",
        )
        if path:
            self._emit_context(self.model.open_file(path))

    def _open_recent_item(self, item: QListWidgetItem) -> None:
        project = self._recent_projects[self.recent_list.row(item)]
        self._emit_context(self.model.open_recent(project))

    def _emit_context(self, context: ProjectContext) -> None:
        self.project_opened.emit(context)
        self.accept()
