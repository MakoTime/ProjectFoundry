from projectfoundry.task_runner import TaskRunner, TaskStatus


def test_runner_completes_tasks_in_order_and_reports_progress():
    runner = TaskRunner()
    finished = []
    first = runner.enqueue("First", lambda progress: progress(0.5), finished.append)
    second = runner.enqueue("Second", lambda: "done", finished.append)
    runner.wait_for_done()

    assert first.status is TaskStatus.COMPLETED
    assert first.progress == 1.0
    assert second.result == "done"
    assert [task.name for task in finished] == ["First", "Second"]
    runner.shutdown()


def test_runner_captures_failures():
    runner = TaskRunner()

    def fail():
        raise ValueError("bad input")

    task = runner.enqueue("Failure", fail)
    runner.wait_for_done()

    assert task.status is TaskStatus.FAILED
    assert task.error == "bad input"
    runner.shutdown()


def test_pause_holds_queued_tasks_until_play():
    runner = TaskRunner()
    runner.pause()
    task = runner.enqueue("Paused", lambda: None)

    assert task.status is TaskStatus.PAUSED
    runner.play()
    runner.wait_for_done()

    assert task.status is TaskStatus.COMPLETED
    runner.shutdown()
