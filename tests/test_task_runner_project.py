from threading import current_thread

from projectfoundry.core import BlockObject, Project
from projectfoundry.task_runner import TaskRunner, TaskStatus


class ExampleBlock(BlockObject):
    def prepare(self):
        return self.name

    def process(self, prepared, progress_callback=None):
        return prepared

    def serialise(self, path):
        del path


class BlockWork:
    def __init__(self, block):
        self.block_object = block

    def prepare(self):
        return self.block_object.prepare()

    def process(self, prepared, progress_callback=None):
        return self.block_object.process(prepared, progress_callback)


def test_project_runner_task_uses_block_uid_resolution():
    project = Project()
    block = ExampleBlock("Block")
    project.add_block(block)
    runner = TaskRunner(project)

    task = runner.enqueue_block_task("Block", BlockWork(block))
    runner.wait_for_done()

    assert task.block_uid == block.guid
    assert task.status is TaskStatus.COMPLETED
    runner.shutdown()


def test_project_runner_orders_invalid_uid_dependencies():
    project = Project()
    child = ExampleBlock("Child")
    parent = ExampleBlock("Parent")
    project.add_block(child)
    project.add_block(parent)
    project.connect_blocks(parent.guid, child.guid)
    child.invalidate()
    parent.invalidate()
    runner = TaskRunner(project)
    order = []

    class OrderedWork(BlockWork):
        def prepare(self):
            order.append(f"prepare:{self.block_object.name}")
            return super().prepare()

        def process(self, prepared, progress_callback=None):
            order.append(f"process:{prepared}")
            return super().process(prepared, progress_callback)

    runner.enqueue_block_task("Child", OrderedWork(child))
    parent_task = runner.enqueue_block_task("Parent", OrderedWork(parent))
    runner.wait_for_done()

    assert parent_task.status is TaskStatus.COMPLETED
    assert order == ["prepare:Child", "process:Child", "prepare:Parent", "process:Parent"]
    runner.shutdown()


def test_completion_dispatcher_moves_commit_and_output_to_dispatch_thread():
    project = Project()
    block = ExampleBlock("Block")
    project.add_block(block)
    block.invalidate()
    completion = []
    output_threads = []
    block.add_output_callback(lambda value: output_threads.append(current_thread()))
    runner = TaskRunner(project, completion_dispatcher=completion.append)

    task = runner.enqueue_block_task("Block", BlockWork(block))
    runner.wait_for_done()

    assert task.status is TaskStatus.RUNNING
    assert len(completion) == 1
    assert output_threads == []

    runner._complete_task(*completion[0])

    assert task.status is TaskStatus.COMPLETED
    assert output_threads == [current_thread()]
    runner.shutdown()
