"""PyVista actor adapter for SceneModel."""

from __future__ import annotations

from typing import Any


class PyVistaSceneAdapter:
    """Map scene objects to actors on an injected PyVista-compatible plotter."""

    def __init__(self, plotter: Any, scene_model=None) -> None:
        self.plotter = plotter
        self.scene_model = scene_model
        self.actors: dict[Any, Any] = {}

    def add_object(self, object_base: Any) -> Any:
        payload = getattr(object_base, "scene_data", None)
        if payload is None:
            block_object = getattr(object_base, "block_object", None)
            payload = getattr(block_object, "scene_data", None)
        if payload is None:
            raise ValueError("Object must provide scene_data or block_object.scene_data")
        if object_base in self.actors:
            self.remove_object(object_base)
        object_name = getattr(object_base, "name", "Object")
        object_guid = getattr(object_base, "guid", id(object_base))
        name = f"{object_name}-{object_guid}"
        actor = self.plotter.add_mesh(
            payload,
            name=name,
            reset_camera=False,
        )
        actor.SetVisibility(bool(getattr(object_base, "visible", True)))
        self.actors[object_base] = actor
        if self.scene_model is not None:
            self.scene_model.add_object(object_base)
        return actor

    def remove_object(self, object_base: Any) -> bool:
        actor = self.actors.pop(object_base, None)
        if actor is None:
            return False
        self.plotter.remove_actor(actor)
        if self.scene_model is not None:
            self.scene_model.remove_object(object_base)
        return True

    def set_object_visibility(self, object_base: Any, visible: bool) -> bool:
        actor = self.actors.get(object_base)
        if actor is None:
            return False
        actor.SetVisibility(bool(visible))
        return True

    def clear(self) -> None:
        for object_base in tuple(self.actors):
            self.remove_object(object_base)
