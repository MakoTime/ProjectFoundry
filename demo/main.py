"""Launch the Project Foundry manual integration demo.

Run from the repository root with ``python demo/main.py``.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pyvista as pv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

try:
    from .application import DemoProjectService  # noqa: E402
    from .blocks import register_demo_blocks  # noqa: E402
    from .editor_controller import DemoEditorController  # noqa: E402
except ImportError:
    from application import DemoProjectService  # noqa: E402
    from blocks import register_demo_blocks  # noqa: E402
    from editor_controller import DemoEditorController  # noqa: E402
from PySide6.QtCore import QPoint, Qt, QTimer  # noqa: E402
from PySide6.QtWidgets import (  # noqa: E402
    QApplication,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableView,
    QVBoxLayout,
    QWidget,
)
from pyvistaqt import QtInteractor  # noqa: E402

from projectfoundry import (  # noqa: E402
    ProjectContext,
    ProjectLauncherFactory,
    ProjectSerializer,
    PyVistaSceneAdapter,
    SceneTableManager,
    SceneTableModel,
    SerializerRegistry,
    TaskModel,
    TreeModel,
)
from projectfoundry.dialogs import EditorController  # noqa: E402
from projectfoundry.task_runner import QtTaskRunner, TaskRunner  # noqa: E402
from projectfoundry.tree import Option, TreeNodeMenuFactory  # noqa: E402
from projectfoundry.view_templates.scene_table import SceneTableView  # noqa: E402
from projectfoundry.view_templates.tree import TreeView  # noqa: E402

try:
    from .editors.mesh import ShapeEditorFactory  # noqa: E402
except ImportError:
    from editors.mesh import ShapeEditorFactory  # noqa: E402


class DemoWindow(QMainWindow):
    """Main window for manually exercising the project architecture."""

    def __init__(self, context: ProjectContext, package, serializer, plotter=None) -> None:
        super().__init__()
        self.setWindowTitle("Project Foundry Demo")
        self.resize(1400, 900)
        self.project = context.project
        self.package = package
        self.serializer = serializer
        self._plotter = plotter
        self.scene_table = self.project.scene_table_manager or SceneTableManager(self.project)
        self.scene_table.artifact_loader = pv.read
        self.context = context
        self.task_runner = QtTaskRunner(TaskRunner(self.project), parent=self)
        self.project_service = DemoProjectService(context.project, self.task_runner)
        self.editor_controller = DemoEditorController(
            self.project_service,
            EditorController(ShapeEditorFactory),
        )
        self.root = self.project_service.ensure_mesh_root()
        self._build_widgets()
        self._build_layout()

    def _build_widgets(self) -> None:
        self.tree_view = TreeView(TreeModel([self.root], project=self.project))
        self.tree_view.doubleClicked.connect(self._add_selected_to_scene)
        self.tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self._show_node_menu)

        self.task_model = TaskModel(self.task_runner, self)
        self.task_view = QTableView()
        self.task_view.setModel(self.task_model)

        self.table_model = SceneTableModel(self.scene_table.table_manager, self)
        self.table_view = SceneTableView(self.table_model)
        self.table_view.doubleClicked.connect(self._edit_scene_object)

        self.plotter = (
            self._plotter
            if self._plotter is not None
            else QtInteractor(self, auto_update=False)
        )
        self.plotter.set_background("#465568")
        self.plotter.show_axes()
        self.scene_adapter = None
        QTimer.singleShot(0, self._initialize_scene)

    def _initialize_scene(self) -> None:
        self.scene_table.load_scene_artifacts()
        self.scene_adapter = PyVistaSceneAdapter(
            self.plotter,
            scene_table_manager=self.scene_table,
        )

    def _build_layout(self) -> None:
        task_panel = QWidget()
        task_layout = QVBoxLayout(task_panel)
        self.task_runner_button = QPushButton("Pause tasks")
        self.task_runner_button.clicked.connect(self._toggle_task_runner)
        task_layout.addWidget(self.task_runner_button)
        task_layout.addWidget(self.task_view)

        left_split = QSplitter(Qt.Orientation.Vertical, self)
        left_split.addWidget(self.tree_view)
        left_split.addWidget(task_panel)
        left_split.setStretchFactor(0, 2)
        left_split.setStretchFactor(1, 1)

        right_split = QSplitter(Qt.Orientation.Vertical, self)
        right_split.addWidget(self.plotter.interactor)
        right_split.addWidget(self.table_view)
        right_split.setStretchFactor(0, 4)
        right_split.setStretchFactor(1, 1)

        root_split = QSplitter(Qt.Orientation.Horizontal, self)
        root_split.addWidget(left_split)
        root_split.addWidget(right_split)
        root_split.setStretchFactor(0, 1)
        root_split.setStretchFactor(1, 3)
        self.setCentralWidget(root_split)

    def _add_selected_to_scene(self) -> None:
        node = self.tree_view.selected_node()
        if node is not None and node.object_uid is not None:
            self.project.add_to_scene(node.guid)

    def _toggle_task_runner(self) -> None:
        if self.task_runner.runner.paused:
            self.task_runner.play()
            self.task_runner_button.setText("Pause tasks")
        else:
            self.task_runner.pause()
            self.task_runner_button.setText("Run tasks")

    def _show_node_menu(self, position: QPoint) -> None:
        index = self.tree_view.indexAt(position)
        if not index.isValid():
            return
        self.tree_view.setCurrentIndex(index)
        node = self.tree_view.selected_node()
        if node is None:
            return
        options = TreeNodeMenuFactory.default_options(node)
        if node is self.root:
            options.insert(0, Option("Create Shape", callback=self._create_shape))
        elif node.object_uid is not None:
            options.insert(
                0,
                Option(
                    "Edit Shape",
                    callback=lambda node_uid=node.guid, block_uid=node.object_uid: (
                        self._edit_tree_shape(node_uid, block_uid)
                    ),
                ),
            )
        menu = TreeNodeMenuFactory.create(node, options=options, parent=self.tree_view)
        menu.exec(self.tree_view.viewport().mapToGlobal(position))

    def _create_shape(self) -> None:
        block_uid = self.editor_controller.create_mesh(
            self,
            parent_uid=self.root.guid,
        )
        if block_uid is None:
            return
        self.tree_view.model().refresh()

    def _edit_tree_shape(self, node_uid: str, block_uid: str) -> None:
        if self.editor_controller.edit_mesh(
            self,
            node_uid=node_uid,
            block_uid=block_uid,
        ) is not None:
            self.tree_view.model().refresh()

    def _edit_scene_object(self, index) -> None:
        if not index.isValid():
            return
        row_data = self.table_model.table_manager.get_data()[index.row()]
        scene_object = row_data.obj.obj
        if self.editor_controller.edit_mesh(
            self,
            scene_uid=scene_object.scene_uid,
            block_uid=scene_object.block_uid,
        ) is not None:
            self.tree_view.model().refresh()

    def _shutdown_project(self) -> None:
        self.task_runner.shutdown()
        if self.scene_adapter is not None:
            self.scene_adapter.close()
        self.context.close()

    def _confirm_close(self, event) -> bool:
        if self.task_runner.has_pending_tasks:
            QMessageBox.warning(
                self,
                "Processing in progress",
                "Wait for processing to finish before closing the project.",
            )
            event.ignore()
            return False
        if self.context.dirty:
            decision = QMessageBox.question(
                self,
                "Save project",
                "Save changes before closing?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )
            if decision is QMessageBox.StandardButton.Cancel:
                event.ignore()
                return False
            if decision is QMessageBox.StandardButton.Save:
                self.context.save(self.package, self.serializer)
        return True

    def closeEvent(self, event) -> None:
        if not self._confirm_close(event):
            return
        self._shutdown_project()
        super().closeEvent(event)


def main() -> int:
    app = QApplication(sys.argv)
    app_data = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "ProjectFoundry"
    registry = SerializerRegistry()
    register_demo_blocks(registry)
    serializer = ProjectSerializer(registry)
    launcher = ProjectLauncherFactory.create(
        recent_path=app_data / "recent-projects.json",
        serializer=serializer,
    )
    contexts = []
    launcher.project_opened.connect(contexts.append)
    if launcher.exec() != launcher.DialogCode.Accepted or not contexts:
        return 0
    window = DemoWindow(contexts[0], launcher.model.package, serializer)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())