"""Framework-neutral task state."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol


class TaskStatus(Enum):
    QUEUED = "Queued"
    RUNNING = "Running"
    PAUSED = "Paused"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


class BlockTask(Protocol):
    block_object: object

    def prepare(self) -> object: ...

    def process(self, prepared: object, progress_callback=None) -> object: ...

    def commit(self, prepared: object | None = None) -> object: ...


@dataclass
class Task:
    """A unit of work and its observable execution state."""

    name: str
    work: Callable[..., object]
    on_finished: Callable[[Task], None] | None = None
    task_id: int = field(default=0)
    status: TaskStatus = TaskStatus.QUEUED
    progress: float = 0.0
    result: object = None
    error: str | None = None
    block_uid: str | None = None

    def set_progress(self, progress: float) -> None:
        self.progress = max(0.0, min(1.0, float(progress)))
