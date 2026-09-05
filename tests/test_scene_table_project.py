from projectfoundry.core import BlockObject, Project, ProjectEventKind
from projectfoundry.scene_table import SceneTableManager, SceneTableModel


class ExampleBlock(BlockObject):
    def prepare(self):
        return None

    def process(self, prepared, progress_callback=None):
        return prepared

    def serialise(self, path):
        del path


def test_project_table_removal_delegates_scene_membership_to_project():
    project = Project()
    manager = SceneTableManager(project)
    block = ExampleBlock("Object")
    project.add_block(block)
    project.add_to_scene(block.guid)

    assert manager.remove_block(block.guid)
    assert manager.scene_block_uids == []
    assert manager.table_manager.get_data() == []


def test_project_routes_block_scene_request_to_coupled_scene_table_manager():
    project = Project()
    block = ExampleBlock("Object")
    project.add_block(block)
    manager = SceneTableManager(project)

    project.add_to_scene(block.guid)

    assert manager.scene_block_uids == [block.guid]
    assert manager.scene_objects[block.guid].block_uid == block.guid
    assert len(manager.table_manager.get_data()) == 1


def test_scene_table_model_updates_when_project_adds_block_to_scene():
    project = Project()
    block = ExampleBlock("Object")
    project.add_block(block)
    manager = SceneTableManager(project)
    model = SceneTableModel(manager.table_manager)

    project.add_to_scene(block.guid)

    assert model.rowCount() == 1
    assert model.data(model.index(0, model.NAME)) == "Object"


def test_scene_table_manager_emits_and_releases_scene_objects():
    project = Project()
    block = ExampleBlock("Object")
    project.add_block(block)
    manager = SceneTableManager(project)
    events = []
    manager.add_event_callback(lambda event, scene_object: events.append((event, scene_object)))

    scene_object = manager.add_block(block.guid)
    assert events == [(ProjectEventKind.SCENE_OBJECT_CREATED, scene_object)]

    assert manager.remove_block(block.guid)
    assert events[-1] == (ProjectEventKind.SCENE_OBJECT_REMOVED, scene_object)
    assert scene_object.scene_data is None


def test_scene_table_manager_refreshes_scene_object():
    project = Project()
    block = ExampleBlock("Object")
    project.add_block(block)
    manager = SceneTableManager(project)
    scene_object = manager.add_block(block.guid)
    events = []
    manager.add_event_callback(lambda event, value: events.append((event, value)))

    manager.refresh_block(block.guid)

    assert events == [
        (ProjectEventKind.SCENE_OBJECT_CREATED, scene_object),
        (ProjectEventKind.SCENE_OBJECT_REFRESHED, scene_object),
    ]


def test_block_events_refresh_or_invalidate_scene_object():
    project = Project()
    block = ExampleBlock("Object")
    project.add_block(block)
    manager = SceneTableManager(project)
    scene_object = manager.add_block(block.guid)
    events = []
    manager.add_event_callback(lambda event, value: events.append((event, value)))

    block.commit()
    block.invalidate()

    assert events == [
        (ProjectEventKind.SCENE_OBJECT_CREATED, scene_object),
        (ProjectEventKind.SCENE_OBJECT_REFRESHED, scene_object),
        (ProjectEventKind.BLOCK_INVALIDATED, scene_object),
    ]
