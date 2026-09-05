"""Factory for the demo mesh editor."""

from __future__ import annotations

from .model import DemoMeshEditObject
from .view import ShapeEditorView


class ShapeEditorFactory:
    """Create a mesh editor hosted by a modal dialog."""

    @staticmethod
    def create(
        parent=None,
        *,
        project=None,
        block_uid=None,
        node_uid=None,
        scene_uid=None,
        parent_node_uid=None,
    ) -> tuple[ShapeEditorView, DemoMeshEditObject]:
        model = DemoMeshEditObject(
            project=project,
            block_uid=block_uid,
            node_uid=node_uid,
            scene_uid=scene_uid,
            parent_node_uid=parent_node_uid,
        )
        view = ShapeEditorView(model, parent)
        view.setWindowTitle("Edit Shape" if model.block_uid is not None else "Create Shape")
        view.resize(900, 600)
        return view, model

    @staticmethod
    def select_shape(parent=None, **target) -> tuple[str, str] | None:
        """Open the mesh editor and return its validated values, if accepted."""
        dialog, model = ShapeEditorFactory.create(parent, **target)
        if dialog.exec() != dialog.DialogCode.Accepted:
            dialog.deleteLater()
            return None
        values = model.values()
        dialog.deleteLater()
        return values
