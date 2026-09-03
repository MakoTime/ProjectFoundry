"""Dependency-aware processing objects."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from uuid import uuid4


class BlockObject(ABC):
    """A processing node with explicit dependency and lifecycle semantics."""

    def __init__(self, name: str = "", guid: str | None = None, comments: str = "") -> None:
        self.name = name
        self.guid = guid or str(uuid4())
        self.comments = comments
        self._project = None
        self._valid = True
        self._destroyed = False
        self._invalidation_callbacks: list[Callable[[BlockObject], None]] = []
        self._change_callbacks: list[Callable[[BlockObject], None]] = []
        self._destruction_callbacks: list[Callable[[BlockObject], None]] = []
        self._parents: list[BlockObject] = []
        self._change_parents: list[BlockObject] = []
        self._children: list[BlockObject] = []
        self._change_children: list[BlockObject] = []
        self._parent_dependencies: dict[BlockObject, bool] = {}

    def __hash__(self) -> int:
        return hash(self.guid)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, BlockObject) and self.guid == other.guid

    @property
    def child_block_objects(self) -> tuple[BlockObject, ...]:
        return tuple(self._children)

    @property
    def relationship_child_block_objects(self) -> tuple[BlockObject, ...]:
        return tuple(dict.fromkeys((*self._children, *self._change_children)))

    def is_valid(self) -> bool:
        return self._valid

    def is_destroyed(self) -> bool:
        return self._destroyed

    def invalidate(self, force: bool = False) -> None:
        self._invalidate(set(), force)

    def _invalidate(self, visited: set[BlockObject], force: bool) -> None:
        if self in visited or (not force and not self._valid):
            return
        visited.add(self)
        self._valid = False
        for callback in tuple(self._invalidation_callbacks):
            callback(self)
        for parent in (*self._parents, *self._change_parents):
            parent._invalidate(visited, force)

    def mark_changed(self) -> bool:
        if self._destroyed:
            return False
        self._mark_changed({}, invalidates=True)
        return True

    def _mark_changed(self, visited: dict[BlockObject, bool], invalidates: bool) -> None:
        previous = visited.get(self, False)
        if self in visited and (previous or not invalidates):
            return
        visited[self] = previous or invalidates
        if invalidates:
            self._valid = False
            for callback in tuple(self._invalidation_callbacks):
                callback(self)
        for callback in tuple(self._change_callbacks):
            callback(self)
        for parent in (*self._parents, *self._change_parents):
            parent._mark_changed(visited, invalidates=True)

    def add_parent_block_object(self, parent: BlockObject, dependent: bool = False) -> None:
        if parent is self:
            raise ValueError("A block object cannot be its own parent")
        if parent not in self._parents:
            self._parents.append(parent)
        self._parent_dependencies[parent] = bool(dependent)
        if self not in parent._children:
            parent._children.append(self)

    def remove_parent_block_object(self, parent: BlockObject) -> None:
        if parent in self._parents:
            self._parents.remove(parent)
        self._parent_dependencies.pop(parent, None)
        if self in parent._children:
            parent._children.remove(self)

    def add_child_block_object(self, child: BlockObject, dependent: bool = False) -> None:
        if self._project is not None:
            self._project.add_block(child)
            return self._project.connect_blocks(
                self.guid,
                child.guid,
                dependent=dependent,
            )
        child.add_parent_block_object(self, dependent)

    def remove_child_block_object(self, child: BlockObject) -> None:
        child.remove_parent_block_object(self)

    def add_change_child_block_object(self, child: BlockObject) -> None:
        if self not in child._change_parents:
            child._change_parents.append(self)
        if child not in self._change_children:
            self._change_children.append(child)

    def remove_change_child_block_object(self, child: BlockObject) -> None:
        if self in child._change_parents:
            child._change_parents.remove(self)
        if child in self._change_children:
            self._change_children.remove(child)

    def validate(self) -> None:
        if self._destroyed:
            raise RuntimeError("Cannot validate a destroyed block object")
        self._valid = True

    def add_invalidation_callback(self, callback: Callable[[BlockObject], None]) -> None:
        if callback not in self._invalidation_callbacks:
            self._invalidation_callbacks.append(callback)

    def add_change_callback(self, callback: Callable[[BlockObject], None]) -> None:
        if callback not in self._change_callbacks:
            self._change_callbacks.append(callback)

    def add_destruction_callback(self, callback: Callable[[BlockObject], None]) -> None:
        if callback not in self._destruction_callbacks:
            self._destruction_callbacks.append(callback)

    def destroy(self) -> bool:
        if self._destroyed:
            return False
        self._destroyed = True
        self.invalidate(force=True)
        for callback in tuple(self._destruction_callbacks):
            callback(self)
        for parent in tuple(self._parents):
            dependent = self._parent_dependencies.get(parent, False)
            self.remove_parent_block_object(parent)
            parent._on_child_destroyed(self, dependent)
        for child in tuple(self._children):
            self.remove_child_block_object(child)
        return True

    def _on_child_destroyed(self, child: BlockObject, dependent: bool) -> None:
        del child
        self.mark_changed()
        if dependent:
            self.destroy()

    def commit(self, prepared: object | None = None) -> BlockObject:
        del prepared
        self.validate()
        return self

    @abstractmethod
    def prepare(self) -> object:
        """Prepare inputs for processing."""

    @abstractmethod
    def process(
        self,
        prepared: object,
        progress_callback: Callable[[float], None] | None = None,
    ) -> object:
        """Process prepared inputs."""

    @abstractmethod
    def serialise(self, path: str) -> None:
        """Persist block-owned data to a path."""
