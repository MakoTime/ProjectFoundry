from projectfoundry.core import BlockObject, Project, ProjectEvent
from projectfoundry.scene_table import SceneTableManager


class ExampleBlock(BlockObject):
    def prepare(self):
        return None

    def process(self, prepared, progress_callback=None):
        return prepared

    def serialise(self, path):
        del path


def test_project_emits_mutation_events():
    project = Project()
    events = []
    project.add_event_callback(events.append)
    block = ExampleBlock("Object")
    project.add_block(block)
    SceneTableManager(project)

    project.add_to_scene(block.guid)
    project.select_object(block.guid)
    block.name = "Renamed"
    project.remove_from_scene(block.guid)

    assert [event.kind for event in events] == [
        "block_added",
        "scene_object_created",
        "selection_changed",
        "scene_object_removed",
        "selection_changed",
    ]
    assert all(isinstance(event, ProjectEvent) for event in events)


def test_project_scene_table_manager_receives_scene_requests():
    project = Project()
    block = ExampleBlock("Object")
    project.add_block(block)
    scene = SceneTableManager(project)

    project.add_to_scene(block.guid)

    assert scene.scene_block_uids == [block.guid]
