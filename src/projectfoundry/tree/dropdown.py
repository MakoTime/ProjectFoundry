"""Tree-backed dropdown using the library's factory/model/view pattern."""

from __future__ import annotations

from collections.abc import Iterable

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt
from PySide6.QtWidgets import QComboBox

from .node import TreeNode


class TreeDropdownModel(QAbstractListModel):
    """Flatten tree nodes into selectable rows while retaining node identity."""

    def __init__(self, roots: Iterable[TreeNode], parent=None) -> None:
        super().__init__(parent)
        self._roots = tuple(roots)
        self._items: list[tuple[TreeNode, int]] = []
        self._rebuild_items()

    def _rebuild_items(self) -> None:
        self._items.clear()

        def visit(node: TreeNode, depth: int) -> None:
            self._items.append((node, depth))
            for child in node.children:
                visit(child, depth + 1)

        for root in self._roots:
            visit(root, 0)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._items):
            return None
        node, depth = self._items[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return f"{'  ' * depth}{getattr(node.node_object, 'name', node.name)}"
        if role == Qt.ItemDataRole.UserRole:
            return node
        return None

    def refresh(self) -> None:
        self.beginResetModel()
        self._rebuild_items()
        self.endResetModel()


class TreeDropdownView(QComboBox):
    """Select a tree node while exposing the selected object directly."""

    def selected_node(self) -> TreeNode | None:
        node = self.currentData(Qt.ItemDataRole.UserRole)
        return node if isinstance(node, TreeNode) else None

    def set_selected_node(self, node: TreeNode | None) -> None:
        index = self.findData(node, Qt.ItemDataRole.UserRole)
        self.setCurrentIndex(index)


class TreeDropdownFactory:
    """Construct a tree dropdown from roots and an optional parent widget."""

    @staticmethod
    def create(roots: Iterable[TreeNode], parent=None) -> TreeDropdownView:
        view = TreeDropdownView(parent)
        view.setModel(TreeDropdownModel(roots, view))
        return view
