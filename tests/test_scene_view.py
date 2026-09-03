import pyvista as pv
from PySide6.QtWidgets import QWidget

from projectfoundry.scene import SceneModel
from projectfoundry.view_templates.scene import SceneView, SceneViewFactory


class Plotter:
    def __init__(self):
        self.interactor = QWidget()
        self.actors = []

    def set_background(self, color):
        del color

    def show_axes(self):
        pass

    def add_mesh(self, payload, **kwargs):
        del payload, kwargs
        actor = type("Actor", (), {"SetVisibility": lambda self, value: None})()
        self.actors.append(actor)
        return actor

    def remove_actor(self, actor):
        self.actors.remove(actor)

    def reset_camera(self):
        pass

    def render(self):
        pass


def test_scene_view_factory_creates_pyvista_view():
    scene = SceneModel()
    view = SceneViewFactory.create(scene, plotter=Plotter())

    assert isinstance(view, SceneView)
    assert view.scene_model is scene
    assert view.adapter.scene_model is scene

    view.add_object(type("SceneObject", (), {"scene_data": pv.Sphere()})())
    assert len(view.adapter.actors) == 1
    view.clear()
    view.close()
