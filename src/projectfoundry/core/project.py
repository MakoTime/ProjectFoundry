"""Project composition root and UID-backed registries."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeVar

from ..tree import TreeManager
from .artifacts import ArtifactStore
from .block_object import BlockObject
from .object import EditedObject
from .references import UIDRef

T = TypeVar("T")


class ProjectError(ValueError):
    """Base error for invalid project operations."""


class ProjectEventKind(str, Enum):
    """Typed project and scene lifecycle event names."""

    SCENE_OBJECT_CREATED = "scene_object_created"
    SCENE_OBJECT_REMOVED = "scene_object_removed"
    SCENE_OBJECT_REFRESHED = "scene_object_refreshed"
    SCENE_OBJECT_VISIBILITY_CHANGED = "scene_object_visibility_changed"
    SCENE_OBJECT_TRANSPARENCY_CHANGED = "scene_object_transparency_changed"
    BLOCK_INVALIDATED = "block_invalidated"


@dataclass(frozen=True, slots=True)
class ProjectEvent:
    """A synchronous notification emitted after a Project mutation."""

    kind: ProjectEventKind | str
    uid: str | None = None
    related_uid: str | None = None


class UIDRegistry:
    """Own canonical project items indexed by stable UID."""

    def __init__(self, label: str) -> None:
        self.label = label
        self._items: dict[str, Any] = {}

    def add(self, value: T) -> UIDRef:
        uid = value.guid if hasattr(value, "guid") else value.uid
        if not uid:
            raise ProjectError(f"{self.label} requires a non-empty UID")
        if uid in self._items and self._items[uid] is not value:
            raise ProjectError(f"Duplicate {self.label} UID: {uid}")
        self._items[uid] = value
        return UIDRef(uid)

    def get(self, uid: str) -> T:
        try:
            return self._items[uid]
        except KeyError as error:
            raise ProjectError(f"Unknown {self.label} UID: {uid}") from error

    def remove(self, uid: str) -> T:
        try:
            return self._items.pop(uid)
        except KeyError as error:
            raise ProjectError(f"Unknown {self.label} UID: {uid}") from error

    def contains(self, uid: str) -> bool:
        return uid in self._items

    def values(self) -> tuple[T, ...]:
        return tuple(self._items.values())

    def __len__(self) -> int:
        return len(self._items)


class Project:
    """Own canonical objects and UID-only project relationships."""

    def __init__(
        self,
        artifact_store: ArtifactStore | None = None,
        scene_table_manager=None,
    ) -> None:
        self.objects = UIDRegistry("object")
        self.blocks = UIDRegistry("block")
        self.nodes = UIDRegistry("node")
        self.tree = TreeManager(self)
        self.selected_object_uid: str | None = None
        self._block_children: dict[str, list[str]] = {}
        self._block_parents: dict[str, list[str]] = {}
        self._block_dependencies: dict[tuple[str, str], bool] = {}
        self._event_callbacks: list[Any] = []
        self.artifact_store = artifact_store
        self.scene_table_manager = scene_table_manager

    def shutdown(self) -> None:
        """Release project-owned runtime services before replacement."""
        if self.scene_table_manager is not None:
            self.scene_table_manager.clear()

    def add_event_callback(self, callback) -> None:
        if callback not in self._event_callbacks:
            self._event_callbacks.append(callback)

    def load_block_artifact(self, block_uid: str, loader) -> object:
        """Lazily load a block's disk-backed artifact by block UID."""
        if self.artifact_store is None:
            raise RuntimeError("Project has no artifact store")
        block = self.blocks.get(block_uid)
        if block.block_data.artifact is None:
            raise ValueError(f"Block has no artifact: {block_uid}")
        return self.artifact_store.load(block.block_data.artifact.path, loader)

    def resolve_block(self, uid: str) -> BlockObject:
        """Resolve a block or node UID to its canonical project block."""
        return self.blocks.get(self._resolve_block_uid(uid))

    def remove_event_callback(self, callback) -> None:
        if callback in self._event_callbacks:
            self._event_callbacks.remove(callback)

    def _emit(self, event: ProjectEvent) -> None:
        for callback in tuple(self._event_callbacks):
            callback(event)

    def add_object(
        self,
        object_base: EditedObject,
        *,
        block_uid: str | None = None,
        node_uid: str | None = None,
    ) -> UIDRef:
        if block_uid is None and object_base.block_object is not None:
            block_uid = self.add_block(object_base.block_object).uid
        if block_uid is not None:
            self.blocks.get(block_uid)
        if node_uid is not None:
            self.nodes.get(node_uid)
        if getattr(object_base, "_project", None) not in (None, self):
            raise ProjectError("Object belongs to another project")
        reference = self.objects.add(object_base)
        object_base._project = self
        object_base.block_uid = block_uid
        object_base.node_uid = node_uid
        self._emit(ProjectEvent("object_added", object_base.guid))
        return reference

    def add_block(self, block: BlockObject) -> UIDRef:
        if getattr(block, "_project", None) not in (None, self):
            raise ProjectError("Block belongs to another project")
        reference = self.blocks.add(block)
        block._project = self
        self._block_children.setdefault(block.guid, [])
        self._block_parents.setdefault(block.guid, [])
        self._emit(ProjectEvent("block_added", block.guid))
        return reference

    def add_block_with_node(self, block: BlockObject, node: Any, *, parent_uid: str) -> UIDRef:
        """Add a block and its tree node after validating both project relationships."""
        if getattr(block, "_project", None) not in (None, self):
            raise ProjectError("Block belongs to another project")
        if getattr(node, "_project", None) not in (None, self):
            raise ProjectError("Node belongs to another project")
        if self.blocks.contains(block.guid):
            raise ProjectError(f"Duplicate block UID: {block.guid}")
        if self.nodes.contains(node.guid):
            raise ProjectError(f"Duplicate node UID: {node.guid}")
        self.nodes.get(parent_uid)
        self.add_block(block)
        self.add_node(node, object_uid=block.guid, parent_uid=parent_uid)
        return UIDRef(block.guid)

    def add_node(
        self,
        node: Any,
        *,
        object_uid: str | None = None,
        parent_uid: str | None = None,
    ) -> UIDRef:
        if object_uid is not None:
            if not self.objects.contains(object_uid):
                self.blocks.get(object_uid)
        if parent_uid is not None:
            self.nodes.get(parent_uid)
        if getattr(node, "_project", None) not in (None, self):
            raise ProjectError("Node belongs to another project")
        reference = self.nodes.add(node)
        node._project = self
        node.object_uid = object_uid
        node.parent_uid = parent_uid
        if parent_uid is None:
            self.tree._add_root_node(node)
        else:
            parent = self.nodes.get(parent_uid)
            if node.parent is not parent:
                if node.parent is not None:
                    node.parent.remove_child(node)
                node.parent = parent
            if node not in parent.children:
                parent.children.append(node)
            if node.guid not in parent.child_uids:
                parent.child_uids.append(node.guid)
        self._emit(ProjectEvent("node_added", node.guid, parent_uid))
        return reference

    def connect_blocks(
        self,
        parent_uid: str,
        child_uid: str,
        *,
        dependent: bool = False,
    ) -> UIDRef:
        self.blocks.get(parent_uid)
        self.blocks.get(child_uid)
        if parent_uid == child_uid:
            raise ProjectError("A block cannot be its own child")
        self._ensure_no_block_cycle(parent_uid, child_uid)
        children = self._block_children.setdefault(parent_uid, [])
        if child_uid not in children:
            children.append(child_uid)
        parents = self._block_parents.setdefault(child_uid, [])
        if parent_uid not in parents:
            parents.append(parent_uid)
        self._block_dependencies[(parent_uid, child_uid)] = bool(dependent)
        self._emit(ProjectEvent("blocks_connected", parent_uid, child_uid))
        return UIDRef(child_uid)

    def block_child_uids(self, parent_uid: str) -> tuple[str, ...]:
        self.blocks.get(parent_uid)
        return tuple(self._block_children.get(parent_uid, ()))

    def add_to_scene(self, object_uid: str) -> UIDRef:
        if self.scene_table_manager is None:
            raise ProjectError("Project requires a scene/table manager")
        block_uid = self._resolve_block_uid(object_uid)
        was_present = block_uid in self.scene_table_manager.scene_objects
        self.scene_table_manager.add_block(block_uid)
        if not was_present:
            self._emit(ProjectEvent(ProjectEventKind.SCENE_OBJECT_CREATED, block_uid))
        return UIDRef(block_uid)

    def set_scene_table_manager(self, manager) -> None:
        self.scene_table_manager = manager
        manager.project = self

    def _resolve_block_uid(self, uid: str) -> str:
        if self.blocks.contains(uid):
            return uid
        if self.scene_table_manager is not None:
            for block_uid, scene_object in self.scene_table_manager.scene_objects.items():
                if scene_object.scene_uid == uid:
                    return block_uid
            try:
                row = self.scene_table_manager.table_manager.get_row(uid)
            except (KeyError, ValueError):
                pass
            else:
                return row.obj.obj.block_uid
        if self.objects.contains(uid):
            object_base = self.objects.get(uid)
            block_uid = getattr(object_base, "block_uid", None)
            if block_uid is None and object_base.block_object is not None:
                block_uid = object_base.block_object.guid
            if block_uid is None:
                raise ProjectError(f"Object has no block UID: {uid}")
            self.blocks.get(block_uid)
            return block_uid
        if self.nodes.contains(uid):
            node = self.nodes.get(uid)
            object_uid = getattr(node, "object_uid", None)
            if object_uid is None:
                raise ProjectError(f"Tree node has no object reference: {uid}")
            return self._resolve_block_uid(object_uid)
        raise ProjectError(f"Unknown scene UID: {uid}")

    def add_block_to_scene(self, block_uid: str) -> UIDRef:
        return self.add_to_scene(block_uid)

    def remove_block_from_scene(self, block_uid: str) -> bool:
        if self.scene_table_manager is not None:
            removed = self.scene_table_manager.remove_block(block_uid)
            if removed:
                self._emit(ProjectEvent(ProjectEventKind.SCENE_OBJECT_REMOVED, block_uid))
                if self.selected_object_uid == block_uid:
                    self.selected_object_uid = None
                    self._emit(ProjectEvent("selection_changed", None))
            return removed
        raise ProjectError("Project requires a scene/table manager")

    def remove_from_scene(self, object_uid: str) -> bool:
        return self.remove_block_from_scene(self._resolve_block_uid(object_uid))

    def select_object(self, object_uid: str | None) -> UIDRef | None:
        if object_uid is not None:
            self._resolve_block_uid(object_uid)
        self.selected_object_uid = object_uid
        self._emit(ProjectEvent("selection_changed", object_uid))
        return UIDRef(object_uid) if object_uid is not None else None

    def remove_object(self, object_uid: str) -> EditedObject:
        object_base = self.objects.get(object_uid)
        self.remove_from_scene(object_uid)
        for node in self.nodes.values():
            if getattr(node, "object_uid", None) == object_uid:
                self.remove_node(node.guid)
        block_uid = getattr(object_base, "block_uid", None)
        if block_uid is not None and self.blocks.contains(block_uid):
            self.remove_block(block_uid)
        self.objects.remove(object_uid)
        object_base._project = None
        self._emit(ProjectEvent("object_removed", object_uid))
        return object_base

    def remove_block(self, block_uid: str) -> BlockObject:
        block = self.blocks.get(block_uid)
        for parent_uid in tuple(self._block_parents.get(block_uid, ())):
            self.disconnect_blocks(parent_uid, block_uid)
        for child_uid in tuple(self._block_children.get(block_uid, ())):
            self.disconnect_blocks(block_uid, child_uid)
        self._block_children.pop(block_uid, None)
        self._block_parents.pop(block_uid, None)
        self.blocks.remove(block_uid)
        block._project = None
        self._emit(ProjectEvent("block_removed", block_uid))
        return block

    def remove_node(self, node_uid: str) -> Any:
        node = self.nodes.get(node_uid)
        parent_uid = getattr(node, "parent_uid", None)
        if parent_uid is None:
            self.tree._remove_root_node(node)
        else:
            parent = self.nodes.get(parent_uid)
            if node_uid in parent.child_uids:
                parent.child_uids.remove(node_uid)
            if node in parent.children:
                parent.children.remove(node)
        for child_uid in tuple(getattr(node, "child_uids", ())):
            self.remove_node(child_uid)
        self.nodes.remove(node_uid)
        node._project = None
        self._emit(ProjectEvent("node_removed", node_uid))
        return node

    def rename_object(self, object_uid: str, name: str) -> EditedObject:
        object_base = self.objects.get(object_uid)
        name = str(name).strip()
        if not name:
            raise ProjectError("Object name cannot be empty")
        object_base.name = name
        for node in self.nodes.values():
            if getattr(node, "object_uid", None) == object_uid:
                node.name = name
        self._emit(ProjectEvent("object_renamed", object_uid))
        return object_base

    def rename_block(self, block_uid: str, name: str) -> BlockObject:
        block = self.blocks.get(block_uid)
        name = str(name).strip()
        if not name:
            raise ProjectError("Block name cannot be empty")
        block.name = name
        for node in self.nodes.values():
            if getattr(node, "object_uid", None) == block_uid:
                node.name = name
        if self.scene_table_manager is not None:
            self.scene_table_manager.rename_block(block_uid, name)
        self._emit(ProjectEvent("block_renamed", block_uid))
        return block

    def update_block(self, block_uid: str, *, name: str, block_data) -> BlockObject:
        """Apply validated block data and name as one project mutation."""
        block = self.blocks.get(block_uid)
        name = str(name).strip()
        if not name:
            raise ProjectError("Block name cannot be empty")
        block.name = name
        block.block_data = block_data
        block.mark_changed()
        for node in self.nodes.values():
            if getattr(node, "object_uid", None) == block_uid:
                node.name = name
        if self.scene_table_manager is not None:
            self.scene_table_manager.refresh_block(block_uid)
        self._emit(ProjectEvent("block_updated", block_uid))
        return block

    def disconnect_blocks(self, parent_uid: str, child_uid: str) -> bool:
        children = self._block_children.get(parent_uid, [])
        if child_uid not in children:
            return False
        children.remove(child_uid)
        self._block_parents.get(child_uid, []).remove(parent_uid)
        self._block_dependencies.pop((parent_uid, child_uid), None)
        return True

    def _ensure_no_block_cycle(self, parent_uid: str, child_uid: str) -> None:
        visiting = {parent_uid}
        pending = [child_uid]
        while pending:
            current = pending.pop()
            if current in visiting:
                raise ProjectError("Block relationships contain a cycle")
            visiting.add(current)
            pending.extend(self._block_children.get(current, ()))

    def clear(self) -> None:
        if self.scene_table_manager is not None:
            self.scene_table_manager.clear()
        self.selected_object_uid = None
        self._block_children.clear()
        self._block_parents.clear()
        self._block_dependencies.clear()
        self.objects = UIDRegistry("object")
        self.blocks = UIDRegistry("block")
        self.nodes = UIDRegistry("node")
        self.tree = TreeManager(self)
