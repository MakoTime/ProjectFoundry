"""Qt view for the demo mesh editor."""

from __future__ import annotations

import pyvista as pv
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QDialogButtonBox,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)
from pyvistaqt import QtInteractor

from projectfoundry.dialogs.base.editor import EditorNameMixin
from projectfoundry.dialogs.base.editor.dialog import DialogEditorView

from .model import DemoMeshEditObject

_SHAPE_BUILDERS = {
    "Sphere": pv.Sphere,
    "Cube": pv.Cube,
    "Cone": pv.Cone,
    "Cylinder": pv.Cylinder,
    "Arrow": pv.Arrow,
    "Plane": pv.Plane,
}


class ShapeEditorView(EditorNameMixin, DialogEditorView):
    """Present mesh choices beside a live PyVista preview."""

    def __init__(self, model: DemoMeshEditObject, parent=None) -> None:
        super().__init__(model=model, parent=parent)
        self.shape_combo = QComboBox(self)
        self.shape_combo.addItems(model.shape_options)
        self.preview = QtInteractor(self, auto_update=False)
        self.preview.set_background("#465568")
        controls = QVBoxLayout()
        controls.addWidget(self.create_name_editor())
        controls.addWidget(self.shape_combo)
        controls.addStretch()
        left = QWidget(self)
        left.setLayout(controls)
        content = QHBoxLayout()
        content.addWidget(left)
        content.addWidget(self.preview, stretch=1)
        self._layout.addLayout(content)
        self.create_button_box(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.shape_combo.currentTextChanged.connect(self._shape_changed)
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.timeout.connect(self._show_preview)
        self._preview_closed = False
        self._preview_timer.start(0)

    def _shape_changed(self, shape_type: str) -> None:
        self.model.set_shape_type(shape_type)
        self._show_preview()

    def _show_preview(self) -> None:
        if self._preview_closed:
            return
        self.preview.clear()
        preview_data = _SHAPE_BUILDERS[self.model.shape_type]().copy()
        self.preview.add_mesh(preview_data, reset_camera=False)
        self.preview.reset_camera()
        self.preview.render()

    def _close_preview(self) -> None:
        if self._preview_closed:
            return
        self._preview_closed = True
        self._preview_timer.stop()
        self.preview.close()

    def done(self, result: int) -> None:
        self._close_preview()
        super().done(result)

    def closeEvent(self, event) -> None:
        self._close_preview()
        super().closeEvent(event)
