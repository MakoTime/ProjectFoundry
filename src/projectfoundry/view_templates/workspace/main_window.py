"""Quick-start main-window composition."""

from __future__ import annotations

from collections.abc import Iterable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QSplitter, QVBoxLayout, QWidget

from projectfoundry.project_app import ProjectContext
from projectfoundry.scene import SceneModel
from projectfoundry.scene_table import SceneTableModel, TableManager
from projectfoundry.tree import TreeModel, TreeNode
from projectfoundry.view_templates.scene import SceneView
from projectfoundry.view_templates.scene_table import SceneTableView
from projectfoundry.view_templates.tree import TreeView


class MainWindowTemplate(QMainWindow):
    """Compose tree, scene table, and PyVista scene views for a new project."""

    def __init__(
        self,
        roots: Iterable[TreeNode],
        *,
        project_context: ProjectContext | None = None,
        scene_model: SceneModel | None = None,
        table_manager: TableManager | None = None,
        plotter=None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.project_context = project_context
        self.project = project_context.project if project_context is not None else None
        self.scene_model = scene_model or SceneModel()
        self.table_manager = table_manager or TableManager()
        self.tree_model = TreeModel(list(roots), self)
        self.tree_view = TreeView(self.tree_model)
        self.scene_table_model = SceneTableModel(self.table_manager, self)
        self.scene_table_view = SceneTableView(self.scene_table_model)
        self.scene_view = SceneView(self.scene_model, plotter=plotter)
        self._build_layout()

    def _build_layout(self) -> None:
        left_panel = QWidget(self)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self.tree_view, stretch=2)
        left_layout.addWidget(self.scene_table_view, stretch=1)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.addWidget(left_panel)
        splitter.addWidget(self.scene_view)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        self.setCentralWidget(splitter)


class MainWindowTemplateFactory:
    """Create the standard Project Foundry workspace layout."""

    @staticmethod
    def create(roots: Iterable[TreeNode], **kwargs) -> MainWindowTemplate:
        return MainWindowTemplate(roots, **kwargs)
