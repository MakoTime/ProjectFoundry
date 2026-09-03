from PySide6.QtCore import Qt

from projectfoundry.task_runner import TaskRunner, TaskStatus
from projectfoundry.task_runner.model import TaskModel
from projectfoundry.task_runner.qt_runner import QtTaskRunner


def test_task_model_tracks_qt_runner_state():
    runner = QtTaskRunner(TaskRunner())
    model = TaskModel(runner)
    task = runner.enqueue("Work", lambda progress: progress(0.25))
    runner.wait_for_done()
    runner.task_finished.emit(task)

    assert model.rowCount() == 1
    assert task.status is TaskStatus.COMPLETED
    assert model.data(model.index(0, model.NAME)) == "Work"
    assert model.data(model.index(0, model.STATUS)) == "Completed"
    assert model.data(model.index(0, model.PROGRESS)) == "100%"
    assert model.data(model.index(0, 0), Qt.ItemDataRole.UserRole) is task
    runner.shutdown()
