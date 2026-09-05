"""Small block implementations used only by the manual demo."""

from __future__ import annotations

from typing import Any

import pyvista as pv

from projectfoundry import ArtifactMetadata, BlockData, BlockObject


class DemoMeshData(BlockData):
    shape_type: str = "Sphere"


_SHAPE_BUILDERS = {
    "Sphere": pv.Sphere,
    "Cube": pv.Cube,
    "Cone": pv.Cone,
    "Cylinder": pv.Cylinder,
    "Arrow": pv.Arrow,
    "Plane": pv.Plane,
}


class DemoMeshBlock(BlockObject):
    """A mesh block created from a selected PyVista shape type."""

    type_name = "demo_mesh"

    def __init__(
        self,
        name: str = "Shape",
        shape_type: str = "Sphere",
        guid: str | None = None,
    ) -> None:
        super().__init__(name, guid=guid)
        self.block_data = DemoMeshData(
            shape_type=shape_type,
            artifact=ArtifactMetadata(
                path=f"artifacts/{self.guid}.vtp",
                format="vtp",
            ),
        )

    def prepare(self):
        self._validate_shape_type(self.block_data.shape_type)
        return self.block_data.shape_type

    def process(self, prepared, progress_callback=None):
        if progress_callback is not None:
            progress_callback(0.5)
        self._validate_shape_type(prepared)
        return prepared

    def serialise(self, path: str, result=None) -> None:
        if result is None:
            raise ValueError("A processed shape result is required")
        self._validate_shape_type(result)
        _SHAPE_BUILDERS[result]().save(path)

    def persist_result(self, result, path: str) -> None:
        self.serialise(path, result)

    @staticmethod
    def _validate_shape_type(shape_type: str) -> None:
        if shape_type not in _SHAPE_BUILDERS:
            raise ValueError(f"Unknown demo shape type: {shape_type}")

    def validate(self) -> None:
        self._validate_shape_type(self.block_data.shape_type)
        super().validate()


class DemoMeshTask:
    """Adapt a demo mesh block to the project task-runner contract."""

    def __init__(self, block_object: DemoMeshBlock) -> None:
        self.block_object = block_object

    def prepare(self):
        return self.block_object.prepare()

    def process(self, prepared, progress_callback=None):
        return self.block_object.process(prepared, progress_callback)


def register_demo_blocks(registry: Any) -> None:
    """Register the block types used by the manual demo."""
    registry.register_block(
        DemoMeshBlock.type_name,
        _create_demo_mesh_block,
    )


def _create_demo_mesh_block(record: dict[str, Any]) -> DemoMeshBlock:
    block = DemoMeshBlock(
        record["name"],
        record.get("data", {}).get("shape_type", "Sphere"),
        guid=record["block_uid"],
    )
    block.block_data = DemoMeshData.model_validate(record.get("data", {}))
    return block