"""Demo-specific editor workflows."""

from __future__ import annotations

from projectfoundry.dialogs import EditorController


class DemoEditorController:
    """Coordinate mesh editor dialogs with the demo project service."""

    def __init__(self, project_service, editor_controller: EditorController) -> None:
        self.project_service = project_service
        self.editor_controller = editor_controller

    def create_mesh(self, parent, *, parent_uid: str) -> str | None:
        model = self.editor_controller.open(
            parent,
            project=self.project_service.project,
            parent_node_uid=parent_uid,
        )
        if model is None:
            return None
        name, shape_type = model.values()
        block_uid = self.project_service.create_mesh_item(
            name,
            shape_type,
            parent_uid=parent_uid,
        )
        self.project_service.process_mesh_item(block_uid)
        return block_uid

    def edit_mesh(self, parent, **target) -> str | None:
        model = self.editor_controller.open(
            parent,
            project=self.project_service.project,
            **target,
        )
        if model is None:
            return None
        block_uid = self.project_service.update_mesh_item(model)
        self.project_service.process_mesh_item(block_uid)
        return block_uid
