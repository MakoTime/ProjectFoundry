from types import SimpleNamespace

import pytest

from demo import main as demo_main
from demo.application import DemoProjectService
from demo.blocks import DemoMeshBlock, register_demo_blocks
from demo.editor_controller import DemoEditorController
from demo.editors.mesh.factory import ShapeEditorFactory
from demo.editors.mesh.model import DemoMeshEditObject
from projectfoundry import SerializerRegistry, TreeNode


class FakeProjectService:
    def __init__(self):
        self.project = None
        self.created = None
        self.processed = []

    def create_mesh_item(self, name, shape_type, *, parent_uid):
        self.created = (name, shape_type, parent_uid)
        return "created-block"

    def process_mesh_item(self, block_uid):
        self.processed.append(block_uid)


class FakeModel:
    def __init__(self):
        self.refreshed = False

    def refresh(self):
        self.refreshed = True


class FakeTreeView:
    def __init__(self):
        self._model = FakeModel()

    def model(self):
        return self._model


class FakeEditorController:
    def __init__(self, values):
        self.values = values

    def open(self, parent, **target):
        del parent, target
        return SimpleNamespace(values=lambda: self.values)


def test_demo_editor_controller_creates_and_processes_mesh(monkeypatch):
    class Service:
        project = object()

        def create_mesh_item(self, name, shape_type, *, parent_uid):
            self.created = (name, shape_type, parent_uid)
            return "block-1"

        def process_mesh_item(self, block_uid):
            self.processed = block_uid

    service = Service()
    controller = DemoEditorController(service, FakeEditorController(("Shape", "Cube")))

    assert controller.create_mesh(None, parent_uid="root") == "block-1"
    assert service.created == ("Shape", "Cube", "root")
    assert service.processed == "block-1"


def test_create_shape_routes_created_block_uid_to_processing(monkeypatch):
    values = ("Created", "Sphere")
    project_service = FakeProjectService()
    window = SimpleNamespace(
        project=None,
        project_service=project_service,
        editor_controller=DemoEditorController(
            project_service,
            FakeEditorController(values),
        ),
        root=TreeNode("Meshes", uid="root"),
        tree_view=FakeTreeView(),
    )
    demo_main.DemoWindow._create_shape(window)

    name, shape_type, parent_uid = project_service.created
    assert (name, shape_type) == values
    assert parent_uid == window.root.guid
    assert project_service.processed == ["created-block"]
    assert window.tree_view.model().refreshed


def test_project_service_creates_mesh_block_and_tree_node():
    from projectfoundry import Project, TaskRunner

    project = Project()
    root = TreeNode("Meshes", uid="root")
    project.add_node(root)

    runner = TaskRunner(project)
    block_uid = DemoProjectService(project, runner).create_mesh_item(
        "Created",
        "Cube",
        parent_uid=root.guid,
    )

    block = project.blocks.get(block_uid)
    node = project.nodes.get(root.child_uids[0])
    assert block.block_data.shape_type == "Cube"
    assert node.object_uid == block_uid
    runner.shutdown()


def test_project_service_updates_existing_mesh_block_and_tree_name():
    from projectfoundry import Project

    project = Project()
    root = TreeNode("Meshes", uid="root")
    project.add_node(root)
    runner = type("Runner", (), {})()
    service = DemoProjectService(project, runner)
    block_uid = service.create_mesh_item("Before", "Sphere", parent_uid=root.guid)
    node = project.nodes.get(root.child_uids[0])
    model = DemoMeshEditObject(project=project, block_uid=block_uid)
    model.name = "After"
    model.set_shape_type("Cube")

    service.update_mesh_item(model)

    assert project.blocks.get(block_uid).name == "After"
    assert project.blocks.get(block_uid).block_data.shape_type == "Cube"
    assert node.name == "After"


def test_project_creation_rejects_missing_parent_without_partial_state():
    from projectfoundry import Project

    project = Project()
    block = DemoMeshBlock("Created")
    node = TreeNode("Created")

    with pytest.raises(ValueError, match="Unknown node UID"):
        project.add_block_with_node(block, node, parent_uid="missing")

    assert len(project.blocks) == 0
    assert len(project.nodes) == 0


def test_project_creation_rejects_duplicate_uids_without_partial_state():
    from projectfoundry import Project

    project = Project()
    root = TreeNode("Meshes", uid="root")
    project.add_node(root)
    existing = DemoMeshBlock("Existing", guid="block-1")
    project.add_block(existing)
    node = TreeNode("Duplicate")

    with pytest.raises(ValueError, match="Duplicate block UID"):
        project.add_block_with_node(DemoMeshBlock(guid="block-1"), node, parent_uid=root.guid)

    assert len(project.blocks) == 1
    assert len(project.nodes) == 1
    assert not root.child_uids


def test_project_creation_rejects_cross_project_items():
    from projectfoundry import Project

    first = Project()
    second = Project()
    root = TreeNode("Meshes", uid="root")
    first.add_node(root)
    block = DemoMeshBlock("Created")
    first.add_block(block)
    node = TreeNode("Created")

    with pytest.raises(ValueError, match="belongs to another project"):
        second.add_block_with_node(block, node, parent_uid=root.guid)

    assert len(second.blocks) == 0
    assert len(second.nodes) == 0


def test_mesh_editor_model_returns_validated_draft():
    model = DemoMeshEditObject()
    model.set_shape_type("Arrow")

    assert model.values() == ("Shape", "Arrow")


def test_mesh_editor_model_loads_existing_block_draft():
    from projectfoundry import Project

    project = Project()
    block = DemoMeshBlock("Existing", shape_type="Cube")
    project.add_block(block)

    model = DemoMeshEditObject(project=project, block_uid=block.guid)

    assert model.block_uid == block.guid
    assert model.values() == ("Existing", "Cube")


def test_mesh_editor_factory_returns_draft_and_defers_dialog_destruction(monkeypatch):
    class Dialog:
        DialogCode = SimpleNamespace(Accepted=1)

        def exec(self):
            return self.DialogCode.Accepted

        def deleteLater(self):
            self.deleted = True

    model = DemoMeshEditObject()
    dialog = Dialog()
    monkeypatch.setattr(ShapeEditorFactory, "create", staticmethod(lambda parent: (dialog, model)))

    values = ShapeEditorFactory.select_shape()

    assert values == ("Shape", "Sphere")
    assert dialog.deleted


def test_mesh_editor_factory_returns_none_when_cancelled(monkeypatch):
    class Dialog:
        DialogCode = SimpleNamespace(Accepted=1)

        def exec(self):
            return 0

        def deleteLater(self):
            self.deleted = True

    dialog = Dialog()
    monkeypatch.setattr(
        ShapeEditorFactory,
        "create",
        staticmethod(lambda parent: (dialog, DemoMeshEditObject())),
    )

    assert ShapeEditorFactory.select_shape() is None
    assert dialog.deleted


def test_project_context_detaches_and_can_close_twice(tmp_path):
    from projectfoundry import ArtifactStore, Project, ProjectContext

    project = Project(artifact_store=ArtifactStore(tmp_path))
    context = ProjectContext(tmp_path / "project.pfzip", None, project)
    context.close()
    context.close()
    context.dirty = False

    project.add_block(DemoMeshBlock("After close"))

    assert not context.dirty


def test_scene_table_clear_removes_block_observers():
    from projectfoundry import Project, SceneTableManager

    project = Project()
    manager = SceneTableManager(project)
    block = DemoMeshBlock("Observed")
    project.add_block(block)
    manager.add_block(block.guid)

    manager.clear()

    assert manager._watched_blocks == {}
    assert manager._callbacks == []


def test_scene_table_loads_existing_artifacts_without_events(tmp_path):
    from projectfoundry import ArtifactStore, Project, SceneTableManager

    project = Project(artifact_store=ArtifactStore(tmp_path))
    block = DemoMeshBlock("Restored")
    project.add_block(block)
    block.commit(block.process(block.prepare()), project.artifact_store)
    manager = SceneTableManager(project)
    manager.add_block(block.guid)
    manager.artifact_loader = lambda path: path
    manager.scene_objects[block.guid].scene_data = None
    events = []
    manager.add_event_callback(lambda event, value: events.append(event))
    events.clear()

    manager.load_scene_artifacts()

    assert manager.scene_objects[block.guid].scene_data == tmp_path / block.block_data.artifact.path
    assert events == []


def test_task_runner_shutdown_is_idempotent():
    from projectfoundry import TaskRunner

    runner = TaskRunner()
    runner.shutdown()
    runner.shutdown()


def test_demo_item_integrates_through_processing_scene_save_and_reopen(tmp_path):
    from projectfoundry import (
        ArtifactStore,
        Project,
        ProjectSerializer,
        SceneTableManager,
        TaskRunner,
    )

    project = Project(artifact_store=ArtifactStore(tmp_path))
    scene = SceneTableManager(project, artifact_loader=lambda path: path)
    root = TreeNode("Meshes", uid="root")
    project.add_node(root)
    runner = TaskRunner(project)
    service = DemoProjectService(project, runner)

    block_uid = service.create_mesh_item("Integrated", "Sphere", parent_uid=root.guid)
    task = service.process_mesh_item(block_uid)
    runner.wait_for_done()
    service.finish_task(task)

    assert block_uid in scene.scene_objects
    assert scene.scene_objects[block_uid].scene_data == (
        tmp_path / "artifacts" / f"{block_uid}.vtp"
    )

    registry = SerializerRegistry()
    register_demo_blocks(registry)
    serializer = ProjectSerializer(registry)
    restored = Project(artifact_store=ArtifactStore(tmp_path / "restored-artifacts"))
    serializer.load_document(serializer.project_document(project), restored)

    assert restored.blocks.get(block_uid).name == "Integrated"
    assert restored.nodes.get(root.guid).child_uids
    runner.shutdown()


def test_demo_qt_workflow_reaches_scene_and_table(tmp_path, qapplication):
    import time

    from projectfoundry import ArtifactStore, Project, SceneTableManager, TaskRunner
    from projectfoundry.task_runner import QtTaskRunner, TaskStatus

    project = Project(artifact_store=ArtifactStore(tmp_path))
    scene = SceneTableManager(project, artifact_loader=lambda path: path)
    root = TreeNode("Meshes", uid="root")
    project.add_node(root)
    task_runner = QtTaskRunner(TaskRunner(project))
    service = DemoProjectService(project, task_runner)
    completed = []
    task_runner.task_finished.connect(completed.append)

    block_uid = service.create_mesh_item("Qt item", "Sphere", parent_uid=root.guid)
    task = service.process_mesh_item(block_uid)
    deadline = time.monotonic() + 10
    while not completed and time.monotonic() < deadline:
        qapplication.processEvents()
        time.sleep(0.01)

    assert completed and completed[0] is task
    assert task.status is TaskStatus.COMPLETED
    assert root.child_uids
    assert block_uid in scene.scene_objects
    assert scene.table_manager.get_data()
    task_runner.shutdown()


def test_demo_window_runs_shape_from_pause_to_scene(tmp_path, qapplication, monkeypatch):
    import time

    from PySide6.QtWidgets import QWidget

    from demo.main import DemoWindow
    from projectfoundry import ArtifactStore, Project, ProjectContext

    class FakePlotter(QWidget):
        def __init__(self):
            super().__init__()
            self.interactor = self

        def set_background(self, color):
            del color

        def show_axes(self):
            pass

        def add_mesh(self, payload, **kwargs):
            del payload, kwargs
            return type("Actor", (), {"SetVisibility": lambda self, value: None})()

        def remove_actor(self, actor):
            del actor

    project = Project(artifact_store=ArtifactStore(tmp_path))
    context = ProjectContext(tmp_path / "demo.pfzip", None, project)
    window = DemoWindow(context, object(), object(), plotter=FakePlotter())
    window.editor_controller = DemoEditorController(
        window.project_service,
        FakeEditorController(("Window item", "Cube")),
    )

    window.task_runner_button.click()
    window._create_shape()
    block_uid = project.nodes.get(window.root.child_uids[-1]).object_uid
    assert project.blocks.contains(block_uid)
    assert project.scene_table_manager.scene_objects == {}
    assert window.task_runner_button.text() == "Run tasks"

    window.task_runner_button.click()
    deadline = time.monotonic() + 10
    while block_uid not in project.scene_table_manager.scene_objects:
        qapplication.processEvents()
        if time.monotonic() >= deadline:
            raise AssertionError("Demo window task did not reach the scene")
        time.sleep(0.01)

    assert window.task_runner_button.text() == "Pause tasks"
    assert project.tree.get_root_nodes()[0].child_uids
    assert project.scene_table_manager.table_manager.get_data()
    window._shutdown_project()


def test_scene_table_visibility_toggle_renders_updated_actor():
    from PySide6.QtCore import Qt

    from projectfoundry import Project, SceneTableManager, SceneTableModel
    from projectfoundry.scene import PyVistaSceneAdapter

    class Plotter:
        def __init__(self):
            self.renders = 0

        def add_mesh(self, payload, **kwargs):
            del payload, kwargs
            plotter = self

            class Actor:
                visible = True

                def SetVisibility(self, value):
                    self.visible = value
                    plotter.actor = self

            return Actor()

        def remove_actor(self, actor):
            del actor

        def render(self):
            self.renders += 1

    project = Project()
    scene = SceneTableManager(project)
    block = DemoMeshBlock("Visible")
    block.scene_data = object()
    project.add_block(block)
    scene.add_block(block.guid)
    plotter = Plotter()
    actor = PyVistaSceneAdapter(plotter, scene_table_manager=scene).add_object(
        scene.scene_objects[block.guid]
    )
    plotter.actor = actor
    model = SceneTableModel(scene.table_manager)
    index = model.index(0, model.VISIBLE)

    assert model.setData(index, Qt.CheckState.Unchecked, Qt.ItemDataRole.CheckStateRole)
    assert actor.visible is False
    assert plotter.renders == 4


def test_demo_mesh_prepare_does_not_change_validity():
    block = DemoMeshBlock()
    block.invalidate()

    assert block.prepare() == "Sphere"
    assert not block.is_valid()


def test_demo_mesh_prepare_rejects_invalid_shape_without_validating_block():
    block = DemoMeshBlock()
    block.block_data.shape_type = "Unknown"
    block.invalidate()

    try:
        block.prepare()
    except ValueError as error:
        assert str(error) == "Unknown demo shape type: Unknown"
    else:
        raise AssertionError("Invalid shape should fail preparation")
    assert not block.is_valid()


def test_demo_mesh_failed_persistence_does_not_validate_block(tmp_path, monkeypatch):
    from demo import blocks as demo_blocks
    from projectfoundry import ArtifactStore

    def fail_to_build():
        raise OSError("cannot write mesh")

    block = DemoMeshBlock()
    block.invalidate()
    monkeypatch.setitem(demo_blocks._SHAPE_BUILDERS, "Sphere", fail_to_build)

    try:
        block.commit(block.process(block.prepare()), ArtifactStore(tmp_path))
    except OSError as error:
        assert str(error) == "cannot write mesh"
    else:
        raise AssertionError("Persistence failure should propagate")
    assert not block.is_valid()


def test_demo_mesh_successful_commit_validates_and_persists(tmp_path):
    from projectfoundry import ArtifactStore

    block = DemoMeshBlock()
    block.invalidate()
    result = block.process(block.prepare())

    block.commit(result, ArtifactStore(tmp_path))

    assert block.is_valid()
    assert (tmp_path / block.block_data.artifact.path).is_file()


def test_demo_mesh_registration_restores_artifact_metadata():
    registry = SerializerRegistry()
    register_demo_blocks(registry)

    block = registry.create_block(
        DemoMeshBlock.type_name,
        {
            "name": "Loaded",
            "block_uid": "demo-1",
            "data": {
                "shape_type": "Cube",
                "artifact": {
                    "path": "artifacts/original.vtp",
                    "format": "vtp",
                    "version": 3,
                    "checksum": "abc123",
                    "valid": False,
                },
            },
        },
    )

    assert block.block_data.shape_type == "Cube"
    assert block.block_data.artifact.path == "artifacts/original.vtp"
    assert block.block_data.artifact.version == 3
    assert block.block_data.artifact.checksum == "abc123"
    assert not block.block_data.artifact.valid


def test_demo_mesh_project_document_round_trips_block_data(tmp_path):
    from projectfoundry import ArtifactStore, Project, ProjectSerializer

    registry = SerializerRegistry()
    register_demo_blocks(registry)
    serializer = ProjectSerializer(registry)
    project = Project(artifact_store=ArtifactStore(tmp_path / "artifacts"))
    block = DemoMeshBlock("Saved", "Cone")
    project.add_block(block)
    block.commit(block.process(block.prepare()), project.artifact_store)

    restored_project = Project(artifact_store=ArtifactStore(tmp_path / "restored"))
    serializer.load_document(serializer.project_document(project), restored_project)
    restored = restored_project.blocks.get(block.guid)

    assert restored.name == "Saved"
    assert restored.block_data.shape_type == "Cone"
    assert restored.block_data.artifact.path == block.block_data.artifact.path
    assert restored.block_data.artifact.checksum == block.block_data.artifact.checksum


def test_demo_close_is_blocked_while_processing(monkeypatch):
    class Event:
        ignored = False

        def ignore(self):
            self.ignored = True

    class TaskRunner:
        has_pending_tasks = True

    event = Event()
    window = SimpleNamespace(task_runner=TaskRunner())
    monkeypatch.setattr(demo_main.QMessageBox, "warning", lambda *args: None)

    assert not demo_main.DemoWindow._confirm_close(window, event)

    assert event.ignored


def test_demo_close_saves_before_shutdown(monkeypatch):
    class Event:
        ignored = False

        def ignore(self):
            self.ignored = True

    events = []

    class TaskRunner:
        has_pending_tasks = False

        def shutdown(self):
            events.append("shutdown")

    class Context:
        dirty = True

        def save(self, package, serializer):
            events.append("save")

        def close(self):
            events.append("close")

    class Adapter:
        def close(self):
            events.append("adapter")

    class Plotter:
        pass

    monkeypatch.setattr(
        demo_main.QMessageBox,
        "question",
        lambda *args: demo_main.QMessageBox.StandardButton.Save,
    )
    window = SimpleNamespace(
        task_runner=TaskRunner(),
        context=Context(),
        package=object(),
        serializer=object(),
        scene_adapter=Adapter(),
        plotter=Plotter(),
    )
    assert demo_main.DemoWindow._confirm_close(window, Event())
    demo_main.DemoWindow._shutdown_project(window)

    assert events == ["save", "shutdown", "adapter", "close"]
