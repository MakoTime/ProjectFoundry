"""Framework-neutral tree nodes."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any
from uuid import uuid4


class TreeNode:
    """A hierarchical node that can represent a project object or alias."""

    def __init__(
        self,
        name: str,
        *,
        node_object: Any = None,
        parent: TreeNode | None = None,
        uid: str | None = None,
    ) -> None:
        self.guid = uid or str(uuid4())
        self.uid = self.guid
        self._project = None
        self.name = name
        self.node_object = node_object
        self.parent = parent
        self.children: list[TreeNode] = []
        self.parent_uid: str | None = None
        self.object_uid: str | None = None
        self.child_uids: list[str] = []
        self.expanded = False
        self.is_block_child = False

    @property
    def block_object(self) -> Any:
        return getattr(self.node_object, "block_object", None)

    def add_child(self, child: TreeNode) -> TreeNode:
        if self._project is not None:
            self._project.add_node(
                child,
                object_uid=getattr(child, "object_uid", None),
                parent_uid=self.guid,
            )
            return child
        if child.parent is not None and child.parent is not self:
            child.parent.remove_child(child)
        if child not in self.children:
            self.children.append(child)
        child.parent = self
        if child.guid not in self.child_uids:
            self.child_uids.append(child.guid)
        return child

    def remove_child(self, child: TreeNode) -> bool:
        if self._project is not None and child in self.children:
            self._project.remove_node(child.guid)
            return True
        if child not in self.children:
            return False
        self.children.remove(child)
        child.parent = None
        if child.guid in self.child_uids:
            self.child_uids.remove(child.guid)
        return True

    def remove_object_nodes(self, node_object: Any) -> bool:
        removed = False
        for child in tuple(self.children):
            if child.node_object is node_object:
                self.remove_child(child)
                removed = True
            else:
                removed = child.remove_object_nodes(node_object) or removed
        return removed

    def set_block_child_objects(self, objects: Iterable[Any]) -> tuple[TreeNode, ...]:
        for child in tuple(self.children):
            if child.is_block_child:
                self.remove_child(child)
        block_children = []
        for object_base in objects:
            child = TreeNode(object_base.name, node_object=object_base)
            child.is_block_child = True
            self.add_child(child)
            block_children.append(child)
        return tuple(block_children)

    def get_block_objects(self) -> list[Any]:
        blocks = []
        if self.block_object is not None:
            blocks.append(self.block_object)
        for child in self.children:
            blocks.extend(child.get_block_objects())
        return blocks
