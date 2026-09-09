"""A ready-to-use scene table view."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QSlider, QTableView

from projectfoundry.scene_table import SceneTableModel, TableManager


class SceneTableView(QTableView):
    """Configure a scene table model for common desktop workflows."""

    def __init__(self, model: SceneTableModel, parent=None) -> None:
        super().__init__(parent)
        self.setModel(model)
        self.viewport().setAttribute(Qt.WidgetAttribute.WA_Hover, False)
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setStyleSheet(
            "QTableView::item:hover, QTableView::item:selected "
            "{ background-color: transparent; color: palette(text); }"
        )
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
        header.setSectionResizeMode(SceneTableModel.TRANSPARENCY, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(SceneTableModel.TRANSPARENCY, 140)
        header.setSectionResizeMode(SceneTableModel.SHAPES, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(SceneTableModel.SHAPES, 120)
        header.setSectionResizeMode(SceneTableModel.REMOVE, QHeaderView.ResizeMode.ResizeToContents)
        self.clicked.connect(model.handle_click)
        self.model().modelReset.connect(self._sync_sliders)
        self.model().rowsInserted.connect(self._sync_sliders)
        self.model().rowsRemoved.connect(self._sync_sliders)
        self._sync_sliders()

    def _sync_sliders(self, *args) -> None:
        del args
        model = self.model()
        for row in range(model.rowCount()):
            index = model.index(row, SceneTableModel.TRANSPARENCY)
            slider = self.indexWidget(index)
            if slider is None:
                slider = QSlider(Qt.Orientation.Horizontal, self)
                slider.setRange(0, 100)
                slider.setToolTip("Set transparency")
                slider.valueChanged.connect(
                    lambda value, index=index: model.setData(
                        index,
                        value / 100,
                        Qt.ItemDataRole.EditRole,
                    )
                )
                self.setIndexWidget(index, slider)
            slider.blockSignals(True)
            value = model.data(index, Qt.ItemDataRole.DisplayRole)
            slider.setValue(round(float(value) * 100))
            slider.blockSignals(False)


class SceneTableViewFactory:
    """Build a scene table view from an existing manager or model."""

    @staticmethod
    def create(source: TableManager | SceneTableModel, parent=None) -> SceneTableView:
        model = source if isinstance(source, SceneTableModel) else SceneTableModel(source)
        return SceneTableView(model, parent)
