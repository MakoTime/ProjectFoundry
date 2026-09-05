"""Base model contract for editable dialogs."""

from __future__ import annotations


class EditorModel:
    """Small common contract for models edited by a workspace view."""

    def validate(self) -> None:
        """Raise a domain error when the current model cannot be applied."""
        return None

    def apply(self):
        """Validate and return the applied model value."""
        self.validate()
        return self


class BlockEditorModel(EditorModel):
    """Base model for editors targeting a project block from any launch context."""

    def __init__(
        self,
        *,
        project=None,
        block_uid: str | None = None,
        node_uid: str | None = None,
        scene_uid: str | None = None,
        parent_node_uid: str | None = None,
        name: str = "",
    ) -> None:
        self.project = project
        self.block_uid = block_uid
        self.node_uid = node_uid
        self.scene_uid = scene_uid
        self.parent_node_uid = parent_node_uid
        self.name = name

    def resolve_target_block(self):
        source_uids = tuple(
            uid
            for uid in (self.block_uid, self.node_uid, self.scene_uid)
            if uid is not None
        )
        if not source_uids:
            return None
        if self.project is None:
            raise RuntimeError("A project is required to resolve a block target")
        blocks = tuple(self.project.resolve_block(uid) for uid in source_uids)
        block = blocks[0]
        if any(candidate.guid != block.guid for candidate in blocks[1:]):
            raise ValueError("Block, node, and scene target UIDs must identify one block")
        return block

    def validate(self) -> None:
        self.name = str(self.name).strip()
        if not self.name:
            raise ValueError("Block name cannot be empty")

    def apply(self):
        self.validate()
        return self
