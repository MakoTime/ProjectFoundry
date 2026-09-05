"""PySide6 adapter for the framework-neutral task runner."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from .runner import TaskRunner
from .task import Task


class QtTaskRunner(QObject):
    """Bridge task-runner callbacks onto Qt signals."""

    task_added = Signal(object)
    task_updated = Signal(object)
    task_finished = Signal(object)
    _completion_requested = Signal(object)

    def __init__(self, runner: TaskRunner | None = None, parent=None) -> None:
        super().__init__(parent)
        self.runner = runner or TaskRunner()
        self.runner.completion_dispatcher = self._completion_requested.emit
        self._completion_requested.connect(self._complete_task)
        self.runner.add_task_added_callback(self.task_added.emit)
        self.runner.add_task_updated_callback(self.task_updated.emit)
        self.runner.add_task_finished_callback(self.task_finished.emit)

    def enqueue(self, *args, **kwargs) -> Task:
        return self.runner.enqueue(*args, **kwargs)

    def enqueue_block_task(self, *args, **kwargs) -> Task:
        return self.runner.enqueue_block_task(*args, **kwargs)

    def _complete_task(self, completion) -> None:
        task, future = completion
        self.runner._complete_task(task, future)

    def pause(self) -> None:
        self.runner.pause()

    @property
    def has_pending_tasks(self) -> bool:
        return self.runner.has_pending_tasks

    def play(self) -> None:
        self.runner.play()

    def cancel(self, task: Task) -> bool:
        return self.runner.cancel(task)

    def wait_for_done(self, timeout: float | None = None) -> bool:
        return self.runner.wait_for_done(timeout)

    def shutdown(self, wait: bool = True) -> None:
        self.runner.shutdown(wait)
