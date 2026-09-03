"""Ready-to-use Qt tree view."""

from __future__ import annotations

from PySide6.QtCore import QModelIndex
from PySide6.QtWidgets import QAbstractItemView, QTreeView

from projectfoundry.tree import TreeModel, TreeNode


class TreeView(QTreeView):
    """Configure a TreeModel for common project-tree workflows."""

    def __init__(self, model: TreeModel, parent=None) -> None:
        super().__init__(parent)
        self.setModel(model)
        self.setHeaderHidden(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(
            QAbstractItemView.EditTrigger.EditKeyPressed
            | QAbstractItemView.EditTrigger.SelectedClicked
        )
        self.expanded.connect(lambda index: model.set_expanded(index, True))
        self.collapsed.connect(lambda index: model.set_expanded(index, False))

    def selected_node(self) -> TreeNode | None:
        index = self.currentIndex()
        if not index.isValid():
            return None
        node = index.internalPointer()
        return node if isinstance(node, TreeNode) else None

    def select_node(self, node: TreeNode | None) -> None:
        if node is None:
            self.clearSelection()
            return
        index = self._index_for_node(node)
        if index.isValid():
            self.setCurrentIndex(index)
            self.scrollTo(index)

    def _index_for_node(self, target: TreeNode) -> QModelIndex:
        model = self.model()
        if not isinstance(model, TreeModel):
            return QModelIndex()

        def search(node: TreeNode, parent: QModelIndex) -> QModelIndex:
            for row, child in enumerate(node.children):
                index = model.index(row, 0, parent)
                if child is target:
                    return index
                result = search(child, index)
                if result.isValid():
                    return result
            return QModelIndex()

        for row, root in enumerate(model.root_data):
            index = model.index(row, 0)
            if root is target:
                return index
            result = search(root, index)
            if result.isValid():
                return result
        return QModelIndex()


class TreeViewFactory:
    """Build a TreeView from a tree model or root nodes."""

    @staticmethod
    def create(source: TreeModel | list[TreeNode] | tuple[TreeNode, ...], parent=None) -> TreeView:
        model = source if isinstance(source, TreeModel) else TreeModel(source)
        return TreeView(model, parent)
