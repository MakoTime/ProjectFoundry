"""Scene table row contracts and Qt adapter."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QIcon


class BaseColumn(IntEnum):
    NAME = 0
    VISIBLE = 1
    OBJECT = 2
    PROGRESS = 3
    SHAPES = 4
    REMOVE = 5


@dataclass
class CellObject:
    obj: Any
    icon: QIcon = field(default_factory=QIcon)


@dataclass
class NormalizedProgressBar:
    value: float = 0.0


@dataclass
class VisibleField:
    visible: bool
    on_change: Callable[[bool], Any]


@dataclass
class RowData:
    name: str
    visible: VisibleField
    obj: CellObject
    progress: NormalizedProgressBar = field(default_factory=NormalizedProgressBar)
    other: Any = None
    object_uid: str | None = None

    def uid(self) -> str | None:
        return self.object_uid or getattr(self.obj.obj, "guid", None)


class TableManager:
    """Own scene table rows independently of a Qt view."""

    def __init__(self, project=None) -> None:
        self.project = project
        self.table: list[RowData] = []
        self.rows: dict[str, RowData] = {}

    def add_row(self, row_data: RowData) -> RowData:
        if self.project is not None:
            uid = row_data.uid()
            if uid is None:
                raise ValueError("Project-backed table rows require an object UID")
            self.project.objects.get(uid)
            row_data.object_uid = uid
            self.rows[uid] = row_data
            return row_data
        if row_data not in self.table:
            self.table.append(row_data)
        return row_data

    def remove_row(self, row_data: RowData) -> bool:
        if self.project is not None:
            uid = row_data.uid()
            return uid is not None and self.rows.pop(uid, None) is not None
        if row_data not in self.table:
            return False
        self.table.remove(row_data)
        return True

    def get_data(self) -> list[RowData]:
        if self.project is not None:
            return list(self.rows.values())
        return self.table

    def get_row(self, object_uid: str) -> RowData:
        if self.project is None:
            raise ValueError("get_row by UID requires a project-backed table")
        try:
            return self.rows[object_uid]
        except KeyError as error:
            raise KeyError(f"Unknown table object UID: {object_uid}") from error


class SceneTableModel(QAbstractTableModel):
    """Present scene rows and handle visibility/removal interactions."""

    Headers = ["Name", "Visible", "Object", "Progress", "Shapes", "Remove"]
    NAME, VISIBLE, OBJECT, PROGRESS, SHAPES, REMOVE = range(6)

    def __init__(self, table_manager: TableManager, parent=None) -> None:
        super().__init__(parent)
        self.table_manager = table_manager

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.table_manager.get_data())

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        del parent
        return len(self.Headers)

    def add_row(self, row_data: RowData) -> None:
        row = self.rowCount()
        self.beginInsertRows(QModelIndex(), row, row)
        self.table_manager.add_row(row_data)
        self.endInsertRows()

    def add_object(self, object_uid: str, **kwargs) -> RowData:
        if self.table_manager.project is None:
            raise ValueError("add_object requires a project-backed table")
        obj = self.table_manager.project.objects.get(object_uid)
        row_data = RowData(
            name=getattr(obj, "name", object_uid),
            visible=VisibleField(
                bool(getattr(obj, "visible", True)),
                lambda visible: self.table_manager.project.objects.get(object_uid)
                and setattr(obj, "visible", bool(visible)),
            ),
            obj=CellObject(None),
            object_uid=object_uid,
            **kwargs,
        )
        self.add_row(row_data)
        return row_data

    def remove_row(self, row: int) -> bool:
        if not 0 <= row < self.rowCount():
            return False
        row_data = self.table_manager.get_data()[row]
        object_base = self._object_for_row(row_data)
        self.beginRemoveRows(QModelIndex(), row, row)
        self.table_manager.remove_row(row_data)
        self.endRemoveRows()
        if self.table_manager.project is not None:
            self.table_manager.project.remove_from_scene(row_data.uid())
        else:
            remove_from_scene = getattr(object_base, "remove_from_scene", None)
            if remove_from_scene is not None:
                remove_from_scene()
        return True

    def remove_object(self, object_base: Any) -> bool:
        if self.table_manager.project is not None:
            object_uid = object_base if isinstance(object_base, str) else object_base.guid
            for row, row_data in enumerate(self.table_manager.get_data()):
                if row_data.uid() == object_uid:
                    return self.remove_row(row)
            return False
        for row, row_data in enumerate(self.table_manager.get_data()):
            if row_data.obj.obj is object_base:
                return self.remove_row(row)
        return False

    def refresh_object(self, object_base: Any) -> bool:
        if self.table_manager.project is not None:
            object_uid = object_base if isinstance(object_base, str) else object_base.guid
            for row, row_data in enumerate(self.table_manager.get_data()):
                if row_data.uid() == object_uid:
                    self.dataChanged.emit(
                        self.index(row, 0),
                        self.index(row, self.columnCount() - 1),
                    )
                    return True
            return False
        for row, row_data in enumerate(self.table_manager.get_data()):
            if row_data.obj.obj is object_base:
                self.dataChanged.emit(self.index(row, 0), self.index(row, self.columnCount() - 1))
                return True
        return False

    def _object_for_row(self, row_data: RowData) -> Any:
        if self.table_manager.project is None:
            return row_data.obj.obj
        return self.table_manager.project.objects.get(row_data.uid())

    def handle_click(self, index: QModelIndex) -> None:
        if index.isValid() and index.column() == self.REMOVE:
            self.remove_row(index.row())

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        row_data = self.table_manager.get_data()[index.row()]
        object_base = self._object_for_row(row_data)
        column = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            if column == self.NAME:
                return getattr(object_base, "name", row_data.name)
            if column == self.OBJECT:
                return object_base
            if column == self.PROGRESS:
                return row_data.progress.value
            if column == self.SHAPES:
                return getattr(object_base, "shape_interface", row_data.other)
            if column == self.REMOVE:
                return "Remove"
        if role == Qt.ItemDataRole.CheckStateRole and column == self.VISIBLE:
            visible = getattr(object_base, "visible", row_data.visible.visible)
            return Qt.CheckState.Checked if visible else Qt.CheckState.Unchecked
        if role == Qt.ItemDataRole.DecorationRole and column == self.OBJECT:
            return row_data.obj.icon
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        flags = super().flags(index)
        if not index.isValid():
            return flags
        if index.column() == self.VISIBLE:
            flags |= Qt.ItemFlag.ItemIsUserCheckable
        if index.column() == self.REMOVE:
            flags |= Qt.ItemFlag.ItemIsEnabled
        return flags

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole) -> bool:
        if not index.isValid() or index.column() != self.VISIBLE:
            return False
        if role not in (Qt.ItemDataRole.CheckStateRole, Qt.ItemDataRole.EditRole):
            return False
        visible = value in (Qt.CheckState.Checked, Qt.CheckState.Checked.value, True)
        row_data = self.table_manager.get_data()[index.row()]
        row_data.visible.visible = visible
        row_data.visible.on_change(visible)
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.CheckStateRole])
        return True

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.Headers[section]
        return None
