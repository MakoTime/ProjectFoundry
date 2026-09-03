"""Ready-to-use PyVista scene view."""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QVBoxLayout, QWidget
from pyvistaqt import QtInteractor

from projectfoundry.scene import PyVistaSceneAdapter, SceneModel


class SceneView(QWidget):
    """Display SceneModel objects through a PyVista Qt interactor."""

    def __init__(self, scene_model: SceneModel | None = None, parent=None, plotter=None) -> None:
        super().__init__(parent)
        self.scene_model = scene_model or SceneModel()
        self.plotter = plotter or QtInteractor(self)
        self.adapter = PyVistaSceneAdapter(self.plotter, self.scene_model)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.plotter.interactor)
        self.plotter.set_background("#465568")
        self.plotter.show_axes()

    def add_object(self, object_base: Any) -> Any:
        return self.adapter.add_object(object_base)

    def remove_object(self, object_base: Any) -> bool:
        return self.adapter.remove_object(object_base)

    def set_object_visibility(self, object_base: Any, visible: bool) -> bool:
        return self.adapter.set_object_visibility(object_base, visible)

    def clear(self) -> None:
        self.adapter.clear()

    def reset_camera(self) -> None:
        self.plotter.reset_camera()
        self.plotter.render()


class SceneViewFactory:
    """Construct a scene view for an optional existing scene model."""

    @staticmethod
    def create(scene_model: SceneModel | None = None, parent=None, plotter=None) -> SceneView:
        return SceneView(scene_model, parent, plotter)
