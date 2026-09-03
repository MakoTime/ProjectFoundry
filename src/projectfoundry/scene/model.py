"""Framework-neutral scene state."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class SceneModel:
    """Own scene membership, selection, and visibility state."""

    def __init__(self, project=None) -> None:
        self.project = project
        self.objects: list[Any] = []
        self.object_uids = project.scene_object_uids if project is not None else []
        self._selected_object: Any = None
        self.selected_object_uid: str | None = None
        self._selection_callbacks: list[Callable[[Any], None]] = []
        self._visibility_callbacks: list[Callable[[Any, bool], None]] = []
        if project is not None:
            project.add_event_callback(self._on_project_event)

    @property
    def selected_object(self) -> Any:
        if self.project is not None and self.selected_object_uid is not None:
            return self.project.objects.get(self.selected_object_uid)
        return self._selected_object

    def add_object(self, object_base: Any) -> Any:
        if self.project is not None:
            self.project.add_to_scene(object_base.guid)
            return object_base
        if object_base not in self.objects:
            self.objects.append(object_base)
        return object_base

    def remove_object(self, object_base: Any) -> bool:
        if self.project is not None:
            removed = self.project.remove_from_scene(object_base.guid)
            if self.selected_object_uid == object_base.guid:
                self.select(None)
            return removed
        if object_base not in self.objects:
            return False
        self.objects.remove(object_base)
        if self.selected_object is object_base:
            self.select(None)
        return True

    def set_object_visibility(self, object_base: Any, visible: bool) -> bool:
        if self.project is not None and object_base.guid not in self.object_uids:
            return False
        if self.project is None and object_base not in self.objects:
            return False
        object_base.visible = bool(visible)
        for callback in tuple(self._visibility_callbacks):
            callback(object_base, object_base.visible)
        return True

    def select(self, object_base: Any) -> Any:
        if self.project is not None:
            object_uid = None if object_base is None else object_base.guid
            self.project.select_object(object_uid)
            self.selected_object_uid = object_uid
            return object_base
        else:
            if object_base is not None and object_base not in self.objects:
                raise ValueError("Cannot select an object that is not in the scene")
            self._selected_object = object_base
        for callback in tuple(self._selection_callbacks):
            callback(object_base)
        return object_base

    def add_selection_callback(self, callback: Callable[[Any], None]) -> None:
        if callback not in self._selection_callbacks:
            self._selection_callbacks.append(callback)

    def _on_project_event(self, event) -> None:
        if event.kind != "selection_changed" or self.project is None:
            return
        self.selected_object_uid = event.uid
        selected = self.selected_object
        for callback in tuple(self._selection_callbacks):
            callback(selected)

    def add_visibility_callback(self, callback: Callable[[Any, bool], None]) -> None:
        if callback not in self._visibility_callbacks:
            self._visibility_callbacks.append(callback)

    def clear(self) -> None:
        if self.project is not None:
            for object_uid in tuple(self.object_uids):
                self.project.remove_from_scene(object_uid)
            self.selected_object_uid = None
            for callback in tuple(self._selection_callbacks):
                callback(None)
            return
        self.objects.clear()
        self.select(None)
