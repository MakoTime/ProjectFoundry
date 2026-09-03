"""Tree root and object-index management."""

from __future__ import annotations

from typing import Any

from .node import TreeNode


class TreeManager:
    """Own the project tree roots independently of a Qt view."""

    def __init__(self, project=None) -> None:
        self.project = project
        self.root_nodes: list[TreeNode] = []

    def add_root_node(self, node: TreeNode) -> TreeNode:
        if self.project is not None and getattr(node, "_project", None) is not self.project:
            self.project.add_node(node)
            return node
        return self._add_root_node(node)

    def _add_root_node(self, node: TreeNode) -> TreeNode:
        if node.parent is not None:
            node.parent.remove_child(node)
        if node not in self.root_nodes:
            self.root_nodes.append(node)
        node.parent = None
        return node

    def remove_root_node(self, node: TreeNode) -> bool:
        if self.project is not None and self.project.nodes.contains(node.guid):
            self.project.remove_node(node.guid)
            return True
        return self._remove_root_node(node)

    def _remove_root_node(self, node: TreeNode) -> bool:
        if node not in self.root_nodes:
            return False
        self.root_nodes.remove(node)
        return True

    def remove_object(self, node_object: Any) -> bool:
        removed = False
        for root in tuple(self.root_nodes):
            if root.node_object is node_object:
                self.remove_root_node(root)
                removed = True
            else:
                removed = root.remove_object_nodes(node_object) or removed
        return removed

    def get_root_nodes(self) -> tuple[TreeNode, ...]:
        return tuple(self.root_nodes)
