"""Reusable application service boundary for project workflows."""

from __future__ import annotations

from projectfoundry.core import BlockObject, Project, UIDRef


class ProjectService:
    """Provide application workflows with one Project mutation boundary."""

    def __init__(self, project: Project, task_runner=None) -> None:
        self.project = project
        self.task_runner = task_runner

    def resolve_block(self, uid: str) -> BlockObject:
        """Resolve any supported project target UID to its canonical block."""
        return self.project.resolve_block(uid)

    def add_block_with_node(
        self,
        block: BlockObject,
        node,
        *,
        parent_uid: str,
    ) -> UIDRef:
        """Register a block and tree node through Project."""
        return self.project.add_block_with_node(block, node, parent_uid=parent_uid)

    def rename_block(self, block_uid: str, name: str) -> BlockObject:
        """Rename a block and let Project synchronize its projections."""
        return self.project.rename_block(block_uid, name)
