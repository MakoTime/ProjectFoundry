"""PyVista actor adapter for SceneModel."""

from __future__ import annotations

from typing import Any

from projectfoundry.core import ProjectEventKind


class PyVistaSceneAdapter:
    """Map scene objects to actors on an injected PyVista-compatible plotter."""

    def __init__(self, plotter: Any, scene_model=None, scene_table_manager=None) -> None:
        self.plotter = plotter
        self.scene_model = scene_model
        self.scene_table_manager = scene_table_manager
        self.actors: dict[Any, Any] = {}
        if scene_table_manager is not None:
            scene_table_manager.add_event_callback(self._on_scene_table_event)

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
        self._render()
        if self.scene_model is not None and self.scene_table_manager is None:
            self.scene_model.add_object(object_base)
        return actor

    def _on_scene_table_event(self, event: ProjectEventKind, scene_object: Any) -> None:
        if event is ProjectEventKind.SCENE_OBJECT_CREATED:
            self.add_object(scene_object)
        elif event is ProjectEventKind.SCENE_OBJECT_REMOVED:
            self.remove_object(scene_object)
        elif event is ProjectEventKind.SCENE_OBJECT_REFRESHED:
            if scene_object in self.actors:
                self.remove_object(scene_object)
            self.add_object(scene_object)
        elif event is ProjectEventKind.SCENE_OBJECT_VISIBILITY_CHANGED:
            actor = self.actors.get(scene_object)
            if actor is not None:
                actor.SetVisibility(scene_object.visible)
                self._render()
        elif event is ProjectEventKind.SCENE_OBJECT_TRANSPARENCY_CHANGED:
            actor = self.actors.get(scene_object)
            if actor is not None and hasattr(actor, "SetOpacity"):
                actor.SetOpacity(scene_object.transparency)

    def remove_object(self, object_base: Any) -> bool:
        actor = self.actors.pop(object_base, None)
        if actor is None:
            return False
        self.plotter.remove_actor(actor)
        self._render()
        if self.scene_model is not None and self.scene_table_manager is None:
            self.scene_model.remove_object(object_base)
        return True

    def set_object_visibility(self, object_base: Any, visible: bool) -> bool:
        actor = self.actors.get(object_base)
        if actor is None:
            return False
        actor.SetVisibility(bool(visible))
        self._render()
        return True

    def _render(self) -> None:
        render = getattr(self.plotter, "render", None)
        if render is not None:
            render()

    def clear(self) -> None:
        for object_base in tuple(self.actors):
            self.remove_object(object_base)

    def close(self) -> None:
        """Detach from the scene table before its project is shut down."""
        if self.scene_table_manager is not None:
            self.scene_table_manager.remove_event_callback(self._on_scene_table_event)
        self.clear()
