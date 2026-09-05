"""Framework-neutral project objects."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import uuid4

from .block_object import BlockData, BlockObject


class EditedObject:
    """A project object with stable identity and explicit lifecycle."""

    type_name = "object"

    def __init__(
        self,
        name: str,
        *,
        guid: str | None = None,
        metadata: dict[str, Any] | None = None,
        block_object: BlockObject | None = None,
        block_data: BlockData | None = None,
        temporary: bool = False,
    ) -> None:
        self.name = name
        self.guid = guid or str(uuid4())
        self.metadata = dict(metadata or {})
        self.block_object = block_object
        self.block_data = block_data or BlockData()
        self.temporary = temporary
        self._project = None
        self.block_uid = getattr(block_object, "guid", None)
        self.node_uid = None
        self._destroyed = False
        self._change_callbacks: list[Callable[[EditedObject], None]] = []
        self._destruction_callbacks: list[Callable[[EditedObject], None]] = []
        if block_object is not None:
            block_object.add_change_callback(self._on_block_changed)
            block_object.add_destruction_callback(self._on_block_destroyed)

    def __hash__(self) -> int:
        return hash(self.guid)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, EditedObject) and self.guid == other.guid

    def is_destroyed(self) -> bool:
        return self._destroyed

    @property
    def project(self):
        if self._project is None:
            raise RuntimeError("Object is not attached to a project")
        return self._project

    def add_to_project(self, project) -> "EditedObject":
        project.add_object(self)
        return self

    def add_to_scene(self):
        self.project.add_to_scene(self.guid)
        return self

    @classmethod
    def from_block_data(cls, block: BlockObject) -> "EditedObject":
        return cls(
            block.name,
            metadata={"block_uid": block.guid},
            block_data=block.block_data.model_copy(deep=True),
            temporary=True,
        )

    def apply_to_block(self, block: BlockObject) -> BlockObject:
        if not self.temporary:
            raise RuntimeError("Only temporary objects can be applied to a block")
        block.block_data = self.block_data.model_copy(deep=True)
        block.name = self.name
        return block

    def add_change_callback(self, callback: Callable[[EditedObject], None]) -> None:
        if callback not in self._change_callbacks:
            self._change_callbacks.append(callback)

    def add_destruction_callback(self, callback: Callable[[EditedObject], None]) -> None:
        if callback not in self._destruction_callbacks:
            self._destruction_callbacks.append(callback)

    def mark_changed(self) -> None:
        if self._destroyed:
            return
        for callback in tuple(self._change_callbacks):
            callback(self)

    def destroy(self) -> bool:
        if self._destroyed:
            return False
        self._destroyed = True
        if (
            not self.temporary
            and self.block_object is not None
            and not self.block_object.is_destroyed()
        ):
            self.block_object.destroy()
        for callback in tuple(self._destruction_callbacks):
            callback(self)
        return True

    def _on_block_changed(self, block: BlockObject) -> None:
        del block
        self.mark_changed()

    def _on_block_destroyed(self, block: BlockObject) -> None:
        del block
        if not self._destroyed:
            self._destroyed = True
            for callback in tuple(self._destruction_callbacks):
                callback(self)
