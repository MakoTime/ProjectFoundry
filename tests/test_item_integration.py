from PySide6.QtCore import Qt

from projectfoundry.core import (
    BlockObject,
    EditedObject,
    Project,
    ProjectSerializer,
    SerializerRegistry,
)
from projectfoundry.scene import PyVistaSceneAdapter
from projectfoundry.scene_table import SceneTableManager, SceneTableModel
from projectfoundry.task_runner import TaskRunner, TaskStatus
from projectfoundry.tree import TreeNode


class ExampleBlock(BlockObject):
    type_name = "ExampleBlock"

    def __init__(self, name):
        super().__init__(name)
        import pyvista as pv

        self.scene_data = pv.Sphere()

    def prepare(self):
        return self.name

    def process(self, prepared, progress_callback=None):
        return prepared

    def serialise(self, path):
        del path


class ExampleObject(EditedObject):
    type_name = "integration-object"


class Actor:
    def __init__(self):
        self.visible = True

    def SetVisibility(self, visible):
        self.visible = visible

    def SetOpacity(self, opacity):
        self.opacity = opacity


class Plotter:
    def __init__(self):
        self.actors = []

    def add_mesh(self, payload, **kwargs):
        del payload, kwargs
        actor = Actor()
        self.actors.append(actor)
        return actor

    def remove_actor(self, actor):
        self.actors.remove(actor)


def test_single_item_flows_through_project_subsystems(tmp_path):
    project = Project()
    block = ExampleBlock("Mesh")
    item = ExampleObject("Mesh", block_object=block)
    project.add_object(item)
    node = TreeNode("Mesh", node_object=item)
    project.add_node(node, object_uid=item.guid)
    scene = SceneTableManager(project)
    table_model = SceneTableModel(scene.table_manager)
    adapter = PyVistaSceneAdapter(Plotter(), scene_table_manager=scene)

    project.add_to_scene(block.guid)
    scene_object = scene.scene_objects[block.guid]
    actor = adapter.actors[scene_object]
    runner = TaskRunner(project)
    task = runner.enqueue("Build mesh", lambda: block.name)
    runner.wait_for_done()

    assert project.objects.get(item.guid) is item
    assert node.object_uid == item.guid
    assert scene.scene_block_uids == [block.guid]
    assert table_model.data(table_model.index(0, table_model.OBJECT)) is scene_object
    assert adapter.actors[scene_object] is actor
    visible_index = table_model.index(0, table_model.VISIBLE)
    assert table_model.setData(visible_index, False, Qt.ItemDataRole.EditRole)
    assert actor.visible is False
    transparency_index = table_model.index(0, table_model.TRANSPARENCY)
    assert table_model.setData(transparency_index, 0.4, Qt.ItemDataRole.EditRole)
    assert actor.opacity == 0.4
    assert task.status is TaskStatus.COMPLETED
    runner.shutdown()


def test_single_item_save_and_load_preserves_identity_and_block(tmp_path):
    registry = SerializerRegistry()
    registry.register_block(
        ExampleBlock.type_name,
        lambda record: ExampleBlock(record["name"]),
    )
    registry.register(
        ExampleObject.type_name,
        lambda record: ExampleObject(
            record["name"],
            block_object=ExampleBlock(record["name"]),
        ),
    )
    serializer = ProjectSerializer(registry)
    project = Project()
    item = ExampleObject("Mesh", block_object=ExampleBlock("Mesh"))
    project.add_object(item)
    path = tmp_path / "item.json"

    serializer.save_project(project, path)
    restored_project = Project()
    restored = serializer.load_into_project(path, restored_project)

    assert restored[0].guid == item.block_object.guid
    assert restored_project.blocks.get(item.block_object.guid) is restored[0]
