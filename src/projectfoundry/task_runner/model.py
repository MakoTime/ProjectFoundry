"""Qt table model for task runner state."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from .qt_runner import QtTaskRunner
from .task import Task


class TaskModel(QAbstractTableModel):
    """Display task state emitted by a Qt task runner."""

    NAME, STATUS, PROGRESS, ERROR = range(4)
    HEADERS = ["Name", "Status", "Progress", "Error"]

    def __init__(self, runner: QtTaskRunner, parent=None) -> None:
        super().__init__(parent)
        self.runner = runner
        self.tasks: list[Task] = []
        runner.task_added.connect(self._task_added)
        runner.task_updated.connect(self._task_updated)
        runner.task_finished.connect(self._task_updated)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.tasks)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        del parent
        return len(self.HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        task = self.tasks[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            values = [task.name, task.status.value, f"{task.progress:.0%}", task.error or ""]
            return values[index.column()]
        if role == Qt.ItemDataRole.UserRole:
            return task
        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.HEADERS[section]
        return None

    def _task_added(self, task: Task) -> None:
        row = len(self.tasks)
        self.beginInsertRows(QModelIndex(), row, row)
        self.tasks.append(task)
        self.endInsertRows()

    def _task_updated(self, task: Task) -> None:
        try:
            row = self.tasks.index(task)
        except ValueError:
            return
        self.dataChanged.emit(self.index(row, 0), self.index(row, self.columnCount() - 1))
