import pytest
import pyvista as pv

from projectfoundry.scene import PyVistaSceneAdapter, SceneModel


class Actor:
    def __init__(self):
        self.visible = True

    def SetVisibility(self, visible):
        self.visible = visible


class Plotter:
    def __init__(self):
        self.added = []
        self.removed = []

    def add_mesh(self, payload, **kwargs):
        self.added.append((payload, kwargs))
        return Actor()

    def remove_actor(self, actor):
        self.removed.append(actor)


class SceneObject:
    def __init__(self, name="Object"):
        self.name = name
        self.guid = "object-guid"
        self.scene_data = pv.Sphere()
        self.visible = True


def test_scene_model_tracks_selection_and_visibility():
    scene = SceneModel()
    obj = SceneObject()
    selected = []
    visibility = []
    scene.add_selection_callback(selected.append)
    scene.add_visibility_callback(lambda value, state: visibility.append((value, state)))
    scene.add_object(obj)

    scene.select(obj)
    scene.set_object_visibility(obj, False)

    assert scene.selected_object is obj
    assert selected == [obj]
    assert visibility == [(obj, False)]


def test_pyvista_adapter_maps_objects_to_actors():
    plotter = Plotter()
    scene = SceneModel()
    adapter = PyVistaSceneAdapter(plotter, scene)
    obj = SceneObject()

    actor = adapter.add_object(obj)
    assert adapter.actors[obj] is actor
    assert scene.objects == [obj]
    assert plotter.added[0][1]["reset_camera"] is False

    assert adapter.set_object_visibility(obj, False)
    assert not actor.visible
    assert adapter.remove_object(obj)
    assert scene.objects == []
    assert plotter.removed == [actor]


def test_pyvista_adapter_requires_renderable_data():
    adapter = PyVistaSceneAdapter(Plotter())
    with pytest.raises(ValueError, match="scene_data"):
        adapter.add_object(object())
