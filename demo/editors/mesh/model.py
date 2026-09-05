"""Temporary mesh editor model for the manual demo."""

from __future__ import annotations

from projectfoundry.dialogs.base.editor import BlockEditorModel
from projectfoundry.dialogs.base.editor.dialog import DialogEditorModel


class DemoMeshEditObject(BlockEditorModel, DialogEditorModel):
    """Hold a validated mesh draft for creation or block editing."""

    SHAPE_TYPES = ("Sphere", "Cube", "Cone", "Cylinder", "Arrow", "Plane")

    def __init__(
        self,
        *,
        project=None,
        block_uid: str | None = None,
        node_uid: str | None = None,
        scene_uid: str | None = None,
        parent_node_uid: str | None = None,
    ) -> None:
        super().__init__(
            project=project,
            block_uid=block_uid,
            node_uid=node_uid,
            scene_uid=scene_uid,
            parent_node_uid=parent_node_uid,
            name="Shape",
        )
        self.shape_type = "Sphere"
        block = self.resolve_target_block()
        if block is not None:
            self.block_uid = block.guid
            self.name = block.name
            self.shape_type = block.block_data.shape_type

    @property
    def shape_options(self) -> tuple[str, ...]:
        return self.SHAPE_TYPES

    def set_shape_type(self, shape_type: str) -> None:
        if shape_type not in self.SHAPE_TYPES:
            raise ValueError(f"Unknown demo shape type: {shape_type}")
        self.shape_type = shape_type

    def validate(self) -> None:
        super().validate()
        if self.shape_type not in self.SHAPE_TYPES:
            raise ValueError(f"Unknown demo shape type: {self.shape_type}")

    def values(self) -> tuple[str, str]:
        self.validate()
        return self.name, self.shape_type
