from projectfoundry.core import (
    BlockObject,
    ObjectBase,
    Project,
    ProjectSerializer,
    SerializerRegistry,
)
from projectfoundry.scene import PyVistaSceneAdapter, SceneModel
from projectfoundry.scene_table import SceneTableModel, TableManager
from projectfoundry.task_runner import TaskRunner, TaskStatus
from projectfoundry.tree import TreeNode


class ExampleBlock(BlockObject):
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


class ExampleObject(ObjectBase):
    type_name = "integration-object"


class Actor:
    def __init__(self):
        self.visible = True

    def SetVisibility(self, visible):
        self.visible = visible


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
    scene = SceneModel(project)
    scene.add_object(item)
    table_model = SceneTableModel(TableManager(project))
    table_model.add_object(item.guid)
    adapter = PyVistaSceneAdapter(Plotter(), scene)

    actor = adapter.add_object(item)
    runner = TaskRunner(project)
    task = runner.enqueue("Build mesh", lambda: block.name)
    runner.wait_for_done()

    assert project.objects.get(item.guid) is item
    assert node.object_uid == item.guid
    assert project.scene_object_uids == [item.guid]
    assert table_model.data(table_model.index(0, table_model.OBJECT)) is item
    assert adapter.actors[item] is actor
    assert task.status is TaskStatus.COMPLETED
    runner.shutdown()


def test_single_item_save_and_load_preserves_identity_and_block(tmp_path):
    registry = SerializerRegistry()
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

    assert restored[0].guid == item.guid
    assert restored[0].block_object.guid == item.block_object.guid
    assert restored_project.blocks.get(item.block_object.guid) is restored[0].block_object
