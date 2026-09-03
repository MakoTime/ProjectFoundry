"""PySide6 model adapter for the framework-neutral tree."""

from __future__ import annotations

import re
from typing import Any

from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt

from .node import TreeNode


class TreeModel(QAbstractItemModel):
    """Expose project tree nodes through Qt's model interface."""

    def __init__(
        self,
        root_data: list[TreeNode] | tuple[TreeNode, ...],
        parent=None,
        duplicate_name_handler=None,
        project=None,
    ):
        super().__init__(parent)
        self.root_data = root_data
        self.duplicate_name_handler = duplicate_name_handler
        self.project = project

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if not parent.isValid():
            return len(self.root_data)
        return len(parent.internalPointer().children)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        del parent
        return 1

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        node = index.internalPointer()
        if role == Qt.ItemDataRole.DisplayRole:
            return getattr(node.node_object, "name", node.name)
        if role == Qt.ItemDataRole.DecorationRole:
            return getattr(node.node_object, "icon", None)
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        flags = super().flags(index)
        if index.isValid() and index.internalPointer().node_object is not None:
            flags |= Qt.ItemFlag.ItemIsEditable
        return flags

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole) -> bool:
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False
        node = index.internalPointer()
        object_base = node.node_object
        if object_base is None:
            return False
        name = str(value).strip()
        if not name:
            return False
        if self.is_name_used(name, exclude=object_base):
            if self.duplicate_name_handler is None:
                return False
            name = self.duplicate_name_handler(name, object_base)
            if name is None:
                return False
        if self.project is not None:
            self.project.rename_object(object_base.guid, name)
        else:
            node.name = name
            object_base.name = name
        if getattr(object_base, "block_object", None) is not None:
            object_base.block_object.name = name
        if hasattr(object_base, "mark_changed"):
            object_base.mark_changed()
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])
        return True

    def names(self, exclude=None) -> set[str]:
        names: set[str] = set()
        seen: set[int] = set()

        def collect(node: TreeNode) -> None:
            object_base = node.node_object
            if object_base is not None and id(object_base) not in seen:
                seen.add(id(object_base))
                if object_base is not exclude:
                    names.add(str(getattr(object_base, "name", node.name)))
            for child in node.children:
                collect(child)

        for root in self.root_data:
            collect(root)
        return names

    def is_name_used(self, name: str, exclude=None) -> bool:
        return str(name).strip() in self.names(exclude=exclude)

    def next_name(self, prefix: str, exclude=None) -> str:
        prefix = str(prefix).strip() or "Object"
        match = re.match(r"^(.*) \d{3}$", prefix)
        if match:
            prefix = match.group(1)
        names = self.names(exclude=exclude)
        if prefix not in names:
            return prefix
        number = 1
        while f"{prefix} {number:03d}" in names:
            number += 1
        return f"{prefix} {number:03d}"

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        if not parent.isValid():
            node = self.root_data[row]
        else:
            node = parent.internalPointer().children[row]
        return self.createIndex(row, column, node)

    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()
        parent_node = index.internalPointer().parent
        if parent_node is None:
            return QModelIndex()
        grandparent = parent_node.parent
        row = (
            self.root_data.index(parent_node)
            if grandparent is None
            else grandparent.children.index(parent_node)
        )
        return self.createIndex(row, 0, parent_node)

    def set_expanded(self, index: QModelIndex, expanded: bool) -> None:
        if index.isValid():
            index.internalPointer().expanded = bool(expanded)

    def is_expanded(self, index: QModelIndex) -> bool:
        return index.isValid() and index.internalPointer().expanded

    def refresh(self) -> None:
        self.beginResetModel()
        self.endResetModel()
