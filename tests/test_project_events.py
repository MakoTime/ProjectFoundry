from projectfoundry.core import ObjectBase, Project, ProjectEvent
from projectfoundry.scene import SceneModel


def test_project_emits_mutation_events():
    project = Project()
    events = []
    project.add_event_callback(events.append)
    obj = ObjectBase("Object")

    project.add_object(obj)
    project.add_to_scene(obj.guid)
    project.select_object(obj.guid)
    project.rename_object(obj.guid, "Renamed")
    project.remove_from_scene(obj.guid)

    assert [event.kind for event in events] == [
        "object_added",
        "scene_object_added",
        "selection_changed",
        "object_renamed",
        "scene_object_removed",
        "selection_changed",
    ]
    assert all(isinstance(event, ProjectEvent) for event in events)


def test_project_scene_model_receives_external_selection_changes():
    project = Project()
    obj = ObjectBase("Object")
    project.add_object(obj)
    project.add_to_scene(obj.guid)
    scene = SceneModel(project)
    selected = []
    scene.add_selection_callback(selected.append)

    project.select_object(obj.guid)

    assert scene.selected_object_uid == obj.guid
    assert scene.selected_object is obj
    assert selected == [obj]
