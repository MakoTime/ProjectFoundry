"""Scene table row contracts and Qt adapter."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any
from uuid import uuid4

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QIcon

from projectfoundry.core.project import ProjectEventKind


def _ignore_transparency_change(value: float) -> None:
    del value


class BaseColumn(IntEnum):
    NAME = 0
    VISIBLE = 1
    OBJECT = 2
    TRANSPARENCY = 3
    SHAPES = 4
    REMOVE = 5


@dataclass
class CellObject:
    obj: Any
    icon: QIcon = field(default_factory=QIcon)


@dataclass
class VisibleField:
    visible: bool
    on_change: Callable[[bool], Any]

@dataclass
class SiderBar:
    value: float = 0.0
    on_change: Callable[[float], Any] = _ignore_transparency_change
    step: float = 0.05
    min: float = 0.0
    max: float = 1.0


@dataclass
class RowData:
    name: str
    visible: VisibleField
    obj: CellObject
    transparency: SiderBar = field(default_factory=SiderBar)
    other: Any = None
    object_uid: str | None = None

    def uid(self) -> str | None:
        return self.object_uid or getattr(self.obj.obj, "guid", None)


@dataclass(eq=False)
class SceneObject:
    block_uid: str
    block_data: Any
    scene_data: Any = None
    scene_uid: str = field(default_factory=lambda: str(uuid4()))
    visible: bool = True
    transparency: float = 1.0

    def set_visibility(self, visible: bool) -> None:
        self.visible = bool(visible)

    def set_transparency(self, transparency: float) -> None:
        self.transparency = float(transparency)


class SceneTableManager:
    """Own coupled persistent scene entries and temporary scene objects."""

    def __init__(self, project=None, artifact_loader=None) -> None:
        self.project = project
        self.artifact_loader = artifact_loader
        self.scene_block_uids: list[str] = []
        self.scene_objects: dict[str, SceneObject] = {}
        self._callbacks: list[Callable[[ProjectEventKind, SceneObject | None], None]] = []
        self._watched_blocks: dict[str, Any] = {}
        self.table_manager = TableManager()
        self.table_manager.scene_table_manager = self
        if project is not None:
            project.set_scene_table_manager(self)

    def _watch_block(self, block) -> None:
        if block.guid in self._watched_blocks:
            return
        block.add_output_callback(self._on_block_output)
        block.add_invalidation_callback(self._on_block_invalidated)
        self._watched_blocks[block.guid] = block

    def _unwatch_block(self, block) -> None:
        block.remove_output_callback(self._on_block_output)
        block.remove_invalidation_callback(self._on_block_invalidated)
        self._watched_blocks.pop(block.guid, None)

    def _on_block_output(self, block) -> None:
        if block.guid in self.scene_objects:
            self.refresh_block(block.guid)

    def _on_block_invalidated(self, block) -> None:
        if block.guid in self.scene_objects:
            self._emit(ProjectEventKind.BLOCK_INVALIDATED, self.scene_objects[block.guid])

    def add_block(
        self,
        block_uid: str,
        *,
        scene_uid: str | None = None,
        visible: bool = True,
        transparency: float = 1.0,
    ) -> SceneObject:
        if self.project is None:
            raise RuntimeError("SceneTableManager requires a project")
        block = self.project.blocks.get(block_uid)
        self._watch_block(block)
        if block_uid in self.scene_objects:
            return self.scene_objects[block_uid]
        scene_data = None
        if self.artifact_loader is not None and block.block_data.artifact is not None:
            scene_data = self.project.load_block_artifact(block_uid, self.artifact_loader)
        if scene_data is None:
            scene_data = getattr(block, "scene_data", None)
        scene_object = SceneObject(
            block_uid=block_uid,
            block_data=block.block_data.model_copy(deep=True),
            scene_data=scene_data,
            scene_uid=scene_uid or str(uuid4()),
            visible=bool(visible),
            transparency=float(transparency),
        )
        self.scene_block_uids.append(block_uid)
        self.scene_objects[block_uid] = scene_object
        self.table_manager.add_row(
            RowData(
                name=block.name,
                visible=VisibleField(scene_object.visible, scene_object.set_visibility),
                obj=CellObject(scene_object),
                transparency=SiderBar(
                    value=scene_object.transparency,
                    on_change=scene_object.set_transparency,
                ),
                object_uid=scene_object.scene_uid,
            )
        )
        self._emit(ProjectEventKind.SCENE_OBJECT_CREATED, scene_object)
        return scene_object

    def remove_block(self, block_uid: str) -> bool:
        scene_object = self.scene_objects.pop(block_uid, None)
        if scene_object is None:
            return False
        self._unwatch_block(self.project.blocks.get(block_uid))
        self.scene_block_uids.remove(block_uid)
        row = next(
            (row for row in self.table_manager.get_data() if row.uid() == scene_object.scene_uid),
            None,
        )
        if row is not None:
            self.table_manager.remove_row(row)
        self._emit(ProjectEventKind.SCENE_OBJECT_REMOVED, scene_object)
        scene_object.scene_data = None
        return True

    def add_event_callback(
        self,
        callback: Callable[[ProjectEventKind, SceneObject | None], None],
    ) -> None:
        if callback not in self._callbacks:
            self._callbacks.append(callback)
            for scene_object in tuple(self.scene_objects.values()):
                callback(ProjectEventKind.SCENE_OBJECT_CREATED, scene_object)

    def remove_event_callback(
        self,
        callback: Callable[[ProjectEventKind, SceneObject | None], None],
    ) -> None:
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def serialized_state(self) -> list[dict[str, Any]]:
        return [
            {
                "scene_uid": self.scene_objects[uid].scene_uid,
                "block_uid": uid,
                "visible": self.scene_objects[uid].visible,
                "transparency": self.scene_objects[uid].transparency,
            }
            for uid in self.scene_block_uids
        ]

    def restore(self, records: list[dict[str, Any]]) -> None:
        for record in records:
            self.add_block(
                record["block_uid"],
                scene_uid=record.get("scene_uid"),
                visible=record.get("visible", True),
                transparency=record.get("transparency", 1.0),
            )

    def refresh_block(self, block_uid: str) -> SceneObject:
        scene_object = self.scene_objects.get(block_uid)
        if scene_object is None:
            raise KeyError(f"Block is not in the scene: {block_uid}")
        block = self.project.blocks.get(block_uid)
        scene_object.block_data = block.block_data.model_copy(deep=True)
        if self.artifact_loader is not None and block.block_data.artifact is not None:
            scene_object.scene_data = self.project.load_block_artifact(
                block_uid,
                self.artifact_loader,
            )
        self._emit(ProjectEventKind.SCENE_OBJECT_REFRESHED, scene_object)
        return scene_object

    def rename_block(self, block_uid: str, name: str) -> bool:
        scene_object = self.scene_objects.get(block_uid)
        if scene_object is None:
            return False
        row = next(
            (row for row in self.table_manager.get_data() if row.uid() == scene_object.scene_uid),
            None,
        )
        if row is None:
            return False
        row.name = name
        self._emit(ProjectEventKind.SCENE_OBJECT_REFRESHED, scene_object)
        return True

    def load_scene_artifacts(self) -> None:
        """Load existing scene payloads without emitting renderer events."""
        if self.project is None or self.artifact_loader is None:
            return
        for block_uid, scene_object in self.scene_objects.items():
            block = self.project.blocks.get(block_uid)
            if block.block_data.artifact is not None:
                scene_object.scene_data = self.project.load_block_artifact(
                    block_uid,
                    self.artifact_loader,
                )

    def set_visibility(self, scene_uid: str, visible: bool) -> bool:
        row = next(
            (row for row in self.table_manager.get_data() if row.uid() == scene_uid),
            None,
        )
        if row is None:
            return False
        scene_object = row.obj.obj
        scene_object.set_visibility(visible)
        self._emit(ProjectEventKind.SCENE_OBJECT_VISIBILITY_CHANGED, scene_object)
        return True

    def set_transparency(self, scene_uid: str, transparency: float) -> bool:
        row = next(
            (row for row in self.table_manager.get_data() if row.uid() == scene_uid),
            None,
        )
        if row is None:
            return False
        scene_object = row.obj.obj
        scene_object.set_transparency(transparency)
        row.transparency.value = scene_object.transparency
        self._emit(ProjectEventKind.SCENE_OBJECT_TRANSPARENCY_CHANGED, scene_object)
        return True

    def _emit(self, event: ProjectEventKind, scene_object: SceneObject | None) -> None:
        for callback in tuple(self._callbacks):
            callback(event, scene_object)

    def clear(self) -> None:
        for block_uid in tuple(self.scene_objects):
            self.remove_block(block_uid)
        self._callbacks.clear()


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

    Headers = ["Name", "Visible", "Object", "Transparency", "Shapes", "Remove"]
    NAME, VISIBLE, OBJECT, TRANSPARENCY, SHAPES, REMOVE = range(6)

    def __init__(self, table_manager: TableManager, parent=None) -> None:
        super().__init__(parent)
        self.table_manager = table_manager
        self.scene_table_manager = getattr(table_manager, "scene_table_manager", None)
        if self.scene_table_manager is not None:
            self.scene_table_manager.add_event_callback(self._scene_table_changed)

    def _scene_table_changed(
        self,
        event: ProjectEventKind,
        scene_object: SceneObject | None,
    ) -> None:
        if scene_object is None:
            self.beginResetModel()
            self.endResetModel()
            return

        row = next(
            (
                row
                for row, row_data in enumerate(self.table_manager.get_data())
                if row_data.uid() == scene_object.scene_uid
            ),
            None,
        )
        if row is None:
            self.beginResetModel()
            self.endResetModel()
            return

        if event == ProjectEventKind.SCENE_OBJECT_VISIBILITY_CHANGED:
            first_column = last_column = self.VISIBLE
        elif event == ProjectEventKind.SCENE_OBJECT_TRANSPARENCY_CHANGED:
            first_column = last_column = self.TRANSPARENCY
        elif event in (
            ProjectEventKind.SCENE_OBJECT_REFRESHED,
            ProjectEventKind.BLOCK_INVALIDATED,
        ):
            first_column = 0
            last_column = self.columnCount() - 1
        else:
            self.beginResetModel()
            self.endResetModel()
            return

        self.dataChanged.emit(
            self.index(row, first_column),
            self.index(row, last_column),
        )

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
                obj.set_visibility,
            ),
            obj=CellObject(None),
            transparency=SiderBar(
                value=float(getattr(obj, "transparency", 1.0)),
                on_change=obj.set_transparency,
            ),
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
        if self.scene_table_manager is not None:
            return self.scene_table_manager.remove_block(object_base.block_uid)
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
        if self.scene_table_manager is not None:
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
            if column == self.TRANSPARENCY:
                return row_data.transparency.value
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
        if not index.isValid() or index.column() not in (self.VISIBLE, self.TRANSPARENCY):
            return False
        if role not in (Qt.ItemDataRole.CheckStateRole, Qt.ItemDataRole.EditRole):
            return False
        if index.column() == self.TRANSPARENCY:
            row_data = self.table_manager.get_data()[index.row()]
            try:
                transparency = max(0.0, min(1.0, float(value)))
            except (TypeError, ValueError):
                return False
            if self.scene_table_manager is not None:
                return self.scene_table_manager.set_transparency(row_data.uid(), transparency)
            row_data.transparency.value = transparency
            row_data.transparency.on_change(transparency)
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])
            return True
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            visible = float(value) > 0
        else:
            visible = value in (Qt.CheckState.Checked, Qt.CheckState.Checked.value, True)
        row_data = self.table_manager.get_data()[index.row()]
        row_data.visible.visible = visible
        if self.scene_table_manager is not None:
            self.scene_table_manager.set_visibility(row_data.uid(), visible)
        else:
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
