import pytest

from projectfoundry.core import BlockObject
from projectfoundry.task_runner import TaskRunner, TaskStatus


class ExampleBlock(BlockObject):
    def prepare(self):
        return self.name

    def process(self, prepared, progress_callback=None):
        if progress_callback is not None:
            progress_callback(0.5)
        return prepared

    def serialise(self, path):
        del path


class ExampleBlockTask:
    def __init__(self, block_object, order):
        self.block_object = block_object
        self.order = order

    def prepare(self):
        self.order.append(f"prepare:{self.block_object.name}")
        return self.block_object.prepare()

    def process(self, prepared, progress_callback=None):
        self.order.append(f"process:{prepared}")
        return self.block_object.process(prepared, progress_callback)

    def commit(self, prepared=None):
        return self.block_object.commit(prepared)


def test_block_tasks_process_invalid_children_before_parent():
    order = []
    child = ExampleBlock("child")
    parent = ExampleBlock("parent")
    parent.add_child_block_object(child)
    child.invalidate()
    parent.invalidate()
    runner = TaskRunner()

    child_task = runner.enqueue_block_task("Child", ExampleBlockTask(child, order))
    parent_task = runner.enqueue_block_task("Parent", ExampleBlockTask(parent, order))
    runner.wait_for_done()

    assert child_task.status is TaskStatus.COMPLETED
    assert parent_task.status is TaskStatus.COMPLETED
    assert order == ["prepare:child", "process:child", "prepare:parent", "process:parent"]
    assert child.is_valid()
    assert parent.is_valid()
    runner.shutdown()


def test_block_task_requires_registered_invalid_child():
    child = ExampleBlock("child")
    parent = ExampleBlock("parent")
    parent.add_child_block_object(child)
    child.invalidate()
    parent.invalidate()
    runner = TaskRunner()

    with pytest.raises(ValueError, match="No block task"):
        runner.enqueue_block_task("Parent", ExampleBlockTask(parent, []))
    runner.shutdown()


def test_block_task_cycle_is_rejected():
    first = ExampleBlock("first")
    second = ExampleBlock("second")
    first.add_child_block_object(second)
    second.add_child_block_object(first)
    runner = TaskRunner()
    first_task = ExampleBlockTask(first, [])
    second_task = ExampleBlockTask(second, [])
    runner.enqueue_block_task("Second", second_task)
    runner.wait_for_done()
    first.invalidate()
    second.invalidate()
    with pytest.raises(ValueError, match="cycle"):
        runner.enqueue_block_task("First", first_task)
    runner.shutdown()
