import pytest

from projectfoundry.core import ObjectBase, Project, ProjectError
from projectfoundry.scene import SceneModel


def test_project_scene_model_stores_only_canonical_object_uids():
    project = Project()
    first = ObjectBase("First")
    second = ObjectBase("Second")
    project.add_object(first)
    project.add_object(second)
    scene = SceneModel(project)

    scene.add_object(first)
    scene.add_object(first)
    scene.add_object(second)

    assert scene.object_uids == [first.guid, second.guid]
    assert scene.object_uids is project.scene_object_uids
    assert scene.objects == []


def test_project_scene_model_resolves_selection_and_cleans_removal():
    project = Project()
    obj = ObjectBase("Object")
    project.add_object(obj)
    scene = SceneModel(project)
    scene.add_object(obj)
    selected = []
    scene.add_selection_callback(selected.append)

    scene.select(obj)
    assert scene.selected_object_uid == obj.guid
    assert project.selected_object_uid == obj.guid
    assert selected == [obj]

    assert scene.remove_object(obj)
    assert project.scene_object_uids == []
    assert scene.selected_object_uid is None


def test_project_scene_model_rejects_unknown_selection():
    project = Project()
    scene = SceneModel(project)

    with pytest.raises(ProjectError):
        scene.select(ObjectBase("Unregistered"))
