"""A ready-to-use scene table view."""

from __future__ import annotations

from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableView

from projectfoundry.scene_table import SceneTableModel, TableManager


class SceneTableView(QTableView):
    """Configure a scene table model for common desktop workflows."""

    def __init__(self, model: SceneTableModel, parent=None) -> None:
        super().__init__(parent)
        self.setModel(model)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(False)
        self.verticalHeader().setVisible(False)
        header = self.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(SceneTableModel.NAME, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(
            SceneTableModel.VISIBLE,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(SceneTableModel.OBJECT, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(
            SceneTableModel.PROGRESS,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(SceneTableModel.SHAPES, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(SceneTableModel.REMOVE, QHeaderView.ResizeMode.ResizeToContents)
        self.clicked.connect(model.handle_click)


class SceneTableViewFactory:
    """Build a scene table view from an existing manager or model."""

    @staticmethod
    def create(source: TableManager | SceneTableModel, parent=None) -> SceneTableView:
        model = source if isinstance(source, SceneTableModel) else SceneTableModel(source)
        return SceneTableView(model, parent)
