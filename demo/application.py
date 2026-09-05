"""Application services for the manual Project Foundry demo."""

from __future__ import annotations

from dataclasses import dataclass

from projectfoundry import Project, TreeNode
from projectfoundry.project_app import ProjectService
from projectfoundry.task_runner import TaskStatus

from .blocks import DemoMeshBlock


@dataclass
class DemoProjectService(ProjectService):
    """Coordinate demo workflows through the Project composition root."""

    project: Project
    task_runner: object
    _processing_blocks: dict[int, str] | None = None

    def __post_init__(self) -> None:
        super().__init__(self.project, self.task_runner)
        self._processing_blocks = {}
        task_finished = getattr(self.task_runner, "task_finished", None)
        if task_finished is not None:
            task_finished.connect(self.finish_task)

    def ensure_mesh_root(self) -> TreeNode:
        """Return the stable mesh root, creating it through Project if needed."""
        root = next(
            (node for node in self.project.tree.get_root_nodes() if node.name == "Meshes"),
            None,
        )
        if root is None:
            root = TreeNode("Meshes", uid="demo-meshes-root")
            self.project.add_node(root)
        return root

    def create_mesh_item(self, name: str, shape_type: str, *, parent_uid: str) -> str:
        block = DemoMeshBlock(name=name, shape_type=shape_type)
        node = TreeNode(block.name)
        self.add_block_with_node(block, node, parent_uid=parent_uid)
        return block.guid

    def update_mesh_item(self, model) -> str:
        model.apply()
        block = model.resolve_target_block()
        if block is None:
            raise ValueError("An existing block is required to update a mesh item")
        block_data = block.block_data.model_copy(
            update={"shape_type": model.shape_type},
            deep=True,
        )
        self.project.update_block(
            block.guid,
            name=model.name,
            block_data=block_data,
        )
        return block.guid

    def process_mesh_item(self, block_uid: str):
        block = self.project.blocks.get(block_uid)
        if block.block_data.artifact is None or block_uid in self._processing_blocks.values():
            return None
        task = self.task_runner.enqueue_block_task(
            f"Process {block.name}",
            self._task_for(block),
        )
        self._processing_blocks[task.task_id] = block_uid
        return task

    def finish_task(self, task) -> None:
        block_uid = self._processing_blocks.pop(task.task_id, None) or task.block_uid
        if block_uid is not None and task.status is TaskStatus.COMPLETED:
            self.project.add_to_scene(block_uid)

    @staticmethod
    def _task_for(block):
        from .blocks import DemoMeshTask

        return DemoMeshTask(block)
