from PySide6.QtCore import Qt

from projectfoundry.core import ObjectBase, Project
from projectfoundry.scene_table import SceneTableModel, TableManager


def test_project_table_owns_rows_by_object_uid():
    project = Project()
    obj = ObjectBase("Object")
    project.add_object(obj)
    manager = TableManager(project)
    model = SceneTableModel(manager)

    row = model.add_object(obj.guid)

    assert row.object_uid == obj.guid
    assert list(manager.rows) == [obj.guid]
    assert manager.get_data()[0] is row
    assert model.data(model.index(0, model.OBJECT)) is obj


def test_project_table_visibility_resolves_canonical_object():
    project = Project()
    obj = ObjectBase("Object")
    project.add_object(obj)
    manager = TableManager(project)
    model = SceneTableModel(manager)
    model.add_object(obj.guid)

    index = model.index(0, model.VISIBLE)
    assert model.setData(index, Qt.CheckState.Unchecked, Qt.CheckStateRole)
    assert obj.visible is False


def test_project_table_removal_delegates_scene_membership_to_project():
    project = Project()
    obj = ObjectBase("Object")
    project.add_object(obj)
    project.add_to_scene(obj.guid)
    manager = TableManager(project)
    model = SceneTableModel(manager)
    model.add_object(obj.guid)

    assert model.remove_object(obj.guid)
    assert not manager.rows
    assert not project.scene_object_uids
    assert project.objects.get(obj.guid) is obj
