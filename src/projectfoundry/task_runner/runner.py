"""Qt-free task scheduling."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from threading import Event, Lock

from .task import BlockTask, Task, TaskStatus


class TaskRunner:
    """Run tasks sequentially while exposing lifecycle callbacks."""

    def __init__(self, project=None, completion_dispatcher=None) -> None:
        self.project = project
        self.completion_dispatcher = completion_dispatcher
        self.tasks: list[Task] = []
        self._next_id = 1
        self._paused = False
        self._resume_event = Event()
        self._resume_event.set()
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="projectfoundry")
        self._futures: dict[int, Future] = {}
        self._completion_events: dict[int, Event] = {}
        self._lock = Lock()
        self._task_added: list[Callable[[Task], None]] = []
        self._task_updated: list[Callable[[Task], None]] = []
        self._task_finished: list[Callable[[Task], None]] = []
        self._block_bindings: dict[str, dict] = {}
        self._closed = False

    @property
    def paused(self) -> bool:
        return self._paused

    @property
    def has_pending_tasks(self) -> bool:
        return any(
            task.status in (TaskStatus.QUEUED, TaskStatus.PAUSED, TaskStatus.RUNNING)
            for task in self.tasks
        )

    def add_task_added_callback(self, callback: Callable[[Task], None]) -> None:
        self._task_added.append(callback)

    def add_task_updated_callback(self, callback: Callable[[Task], None]) -> None:
        self._task_updated.append(callback)

    def add_task_finished_callback(self, callback: Callable[[Task], None]) -> None:
        self._task_finished.append(callback)

    def enqueue(
        self,
        name: str,
        work: Callable[..., object],
        on_finished: Callable[[Task], None] | None = None,
        block_uid: str | None = None,
    ) -> Task:
        with self._lock:
            task = Task(
                name=name,
                work=work,
                on_finished=on_finished,
                task_id=self._next_id,
                block_uid=block_uid,
            )
            self._next_id += 1
            if self._paused:
                task.status = TaskStatus.PAUSED
            self.tasks.append(task)
        self._notify(self._task_added, task)
        self._start_next()
        return task

    def enqueue_block_task(
        self,
        name: str,
        block_task: BlockTask,
        on_finished: Callable[[Task], None] | None = None,
    ) -> Task:
        """Queue invalid block dependencies before the requested block."""
        self._validate_block_task(block_task)
        block_object = block_task.block_object
        if self.project is not None:
            self.project.add_block(block_object)
            block_uid = block_object.guid
        else:
            block_uid = block_object.guid
        if block_object.is_destroyed():
            raise ValueError("Cannot enqueue a task for a destroyed block object")
        binding = self._block_bindings.get(block_object.guid)
        if binding is None:
            binding = {
                "task": block_task,
                "name": name,
                "on_finished": on_finished,
                "prepared": None,
                "block_uid": block_uid,
            }
            self._block_bindings[block_object.guid] = binding
            block_object.add_invalidation_callback(self._block_invalidated)
        else:
            binding.update(task=block_task, name=name, on_finished=on_finished)
        return self._enqueue_block_binding(binding, set())

    @staticmethod
    def _validate_block_task(block_task: BlockTask) -> None:
        if not callable(getattr(block_task, "prepare", None)):
            raise TypeError("Block tasks must implement prepare()")
        process = getattr(block_task, "process", None)
        if not callable(process):
            raise TypeError("Block tasks must implement process(prepared, progress_callback=None)")
        positional = [
            parameter
            for parameter in inspect.signature(process).parameters.values()
            if parameter.kind
            in (parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD)
        ]
        if len(positional) != 2:
            raise TypeError("Block tasks must implement process(prepared, progress_callback=None)")

    def _enqueue_block_binding(self, binding: dict, visiting: set[str]) -> Task:
        block_object = self._resolve_binding_block(binding)
        if binding["block_uid"] in visiting:
            raise ValueError("Block task dependencies contain a cycle")
        visiting.add(binding["block_uid"])
        for child_uid in self._child_uids(block_object):
            if child_uid in visiting:
                raise ValueError("Block task dependencies contain a cycle")
            child = self._resolve_child_block(block_object, child_uid)
            if child.is_destroyed() or child.is_valid():
                continue
            child_binding = self._block_bindings.get(child_uid)
            if child_binding is None:
                raise ValueError(f"No block task is registered for invalid child {child_uid}")
            self._enqueue_block_binding(child_binding, visiting)
        visiting.remove(binding["block_uid"])
        binding["prepared"] = binding["task"].prepare()
        engine_task = self.enqueue(
            binding["name"],
            lambda progress: binding["task"].process(binding["prepared"], progress),
            on_finished=lambda task: self._finish_block_binding(binding, task),
            block_uid=binding["block_uid"],
        )
        return engine_task

    def _block_invalidated(self, block_object) -> None:
        binding = self._block_bindings.get(block_object.guid)
        if binding is not None and not block_object.is_destroyed():
            try:
                self._enqueue_block_binding(binding, set())
            except ValueError:
                return

    def _resolve_binding_block(self, binding: dict):
        if self.project is None:
            return binding["task"].block_object
        return self.project.blocks.get(binding["block_uid"])

    def _child_uids(self, block_object) -> tuple[str, ...]:
        if self.project is not None:
            return self.project.block_child_uids(block_object.guid)
        return tuple(child.guid for child in block_object.child_block_objects)

    def _resolve_child_block(self, parent_block, child_uid: str):
        if self.project is not None:
            return self.project.blocks.get(child_uid)
        return next(child for child in parent_block.child_block_objects if child.guid == child_uid)

    def _finish_block_binding(self, binding: dict, task: Task) -> None:
        if task.status is TaskStatus.COMPLETED:
            try:
                block_object = binding["task"].block_object
                artifact_store = self.project.artifact_store if self.project is not None else None
                block_object.commit(task.result, artifact_store)
                if not block_object.retain_result(task.result):
                    block_object.release_result(task.result)
                    task.result = None
            except Exception as error:
                task.error = str(error)
                task.status = TaskStatus.FAILED
        if binding["on_finished"] is not None:
            binding["on_finished"](task)

    def pause(self) -> None:
        self._paused = True
        self._resume_event.clear()
        for task in self.tasks:
            if task.status is TaskStatus.QUEUED:
                task.status = TaskStatus.PAUSED
                self._notify(self._task_updated, task)

    def play(self) -> None:
        self._paused = False
        self._resume_event.set()
        for task in self.tasks:
            if task.status is TaskStatus.PAUSED:
                task.status = TaskStatus.QUEUED
                self._notify(self._task_updated, task)
        self._start_next()

    def cancel(self, task: Task) -> bool:
        if task.status not in (TaskStatus.QUEUED, TaskStatus.PAUSED):
            return False
        task.status = TaskStatus.CANCELLED
        future = self._futures.get(task.task_id)
        if future is not None:
            future.cancel()
        self._notify(self._task_updated, task)
        self._notify_finished(task)
        self._start_next()
        return True

    def wait_for_done(self, timeout: float | None = None) -> bool:
        futures = tuple(self._futures.values())
        completion_events = tuple(self._completion_events.values())
        for future in futures:
            try:
                future.result(timeout=timeout)
            except Exception:
                pass
        if self.completion_dispatcher is None:
            for completion_event in completion_events:
                completion_event.wait(timeout=timeout)
        return True

    def clear(self) -> None:
        self.pause()
        for task in tuple(self.tasks):
            if task.status in (TaskStatus.QUEUED, TaskStatus.PAUSED):
                self.cancel(task)
        self.tasks.clear()
        self._futures.clear()
        self._completion_events.clear()
        for binding in self._block_bindings.values():
            binding["task"].block_object.remove_invalidation_callback(self._block_invalidated)
        self._block_bindings.clear()
        self._next_id = 1

    def shutdown(self, wait: bool = True) -> None:
        if self._closed:
            return
        self._closed = True
        self.clear()
        self._executor.shutdown(wait=wait, cancel_futures=True)

    def _start_next(self) -> None:
        if self._paused:
            return
        if any(not future.done() for future in self._futures.values()):
            return
        task = next((item for item in self.tasks if item.status is TaskStatus.QUEUED), None)
        if task is None:
            return
        task.status = TaskStatus.RUNNING
        self._notify(self._task_updated, task)
        self._completion_events[task.task_id] = Event()
        future = self._executor.submit(self._run_task, task)
        self._futures[task.task_id] = future
        future.add_done_callback(lambda completed: self._task_done(task, completed))

    def _run_task(self, task: Task) -> object:
        parameters = inspect.signature(task.work).parameters.values()
        accepts_progress = any(
            parameter.kind
            in (parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD)
            for parameter in parameters
        )
        return task.work(task.set_progress) if accepts_progress else task.work()

    def _task_done(self, task: Task, future: Future) -> None:
        if task.status is TaskStatus.CANCELLED:
            self._completion_events.get(task.task_id, Event()).set()
            return
        if self.completion_dispatcher is not None:
            self.completion_dispatcher((task, future))
            return
        self._complete_task(task, future)

    def _complete_task(self, task: Task, future: Future) -> None:
        if task.status is TaskStatus.CANCELLED:
            return
        try:
            task.result = future.result()
        except Exception as error:
            task.error = str(error)
            task.status = TaskStatus.FAILED
        else:
            task.progress = 1.0
            task.status = TaskStatus.COMPLETED
        self._notify(self._task_updated, task)
        self._notify_finished(task)
        if task.status is TaskStatus.COMPLETED:
            with self._lock:
                if task in self.tasks:
                    self.tasks.remove(task)
        self._start_next()
        self._completion_events.get(task.task_id, Event()).set()

    def _notify_finished(self, task: Task) -> None:
        if task.on_finished is not None:
            task.on_finished(task)
        self._notify(self._task_finished, task)

    @staticmethod
    def _notify(callbacks: list[Callable[[Task], None]], task: Task) -> None:
        for callback in tuple(callbacks):
            callback(task)
