"""Registry-driven JSON serialization for project objects."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any


class SerializerRegistry:
    """Register object factories and payload serializers by stable type name."""

    def __init__(self) -> None:
        self._factories: dict[str, Callable[[dict[str, Any]], Any]] = {}
        self._serializers: dict[str, Callable[[Any], dict[str, Any]]] = {}

    def register(
        self,
        type_name: str,
        factory: Callable[[dict[str, Any]], Any],
        serializer: Callable[[Any], dict[str, Any]] | None = None,
    ) -> None:
        if not type_name:
            raise ValueError("A serializer type name is required")
        if type_name in self._factories and self._factories[type_name] is not factory:
            raise ValueError(f"Type already registered: {type_name}")
        self._factories[type_name] = factory
        self._serializers[type_name] = serializer or self._default_serializer

    def create(self, type_name: str, record: dict[str, Any]) -> Any:
        try:
            return self._factories[type_name](record)
        except KeyError as error:
            raise KeyError(f"Unknown serialized type: {type_name}") from error

    def payload(self, type_name: str, value: Any) -> dict[str, Any]:
        try:
            return self._serializers[type_name](value)
        except KeyError as error:
            raise KeyError(f"Unknown serialized type: {type_name}") from error

    @staticmethod
    def _default_serializer(value: Any) -> dict[str, Any]:
        return dict(getattr(value, "metadata", {}))


class ProjectSerializer:
    """Persist registered project objects to a small, versioned JSON document."""

    format_version = 1

    def __init__(self, registry: SerializerRegistry) -> None:
        self.registry = registry

    def save_project(self, project, path: str | Path) -> None:
        """Save all canonical objects from a Project container."""
        self.save(project.objects.values(), path)

    def save(self, objects: Iterable[Any], path: str | Path) -> None:
        records = []
        for value in objects:
            type_name = getattr(value, "type_name", type(value).__name__)
            block_object = getattr(value, "block_object", None)
            project = getattr(value, "_project", None)
            if project is not None and block_object is not None:
                block_child_guids = project.block_child_uids(block_object.guid)
            else:
                block_child_guids = tuple(
                    child.guid
                    for child in getattr(block_object, "child_block_objects", ())
                )
            records.append(
                {
                    "type": type_name,
                    "guid": value.guid,
                    "name": value.name,
                    "block_guid": getattr(block_object, "guid", None),
                    "metadata": dict(getattr(value, "metadata", {})),
                    "payload": self.registry.payload(type_name, value),
                    "block_child_guids": list(block_child_guids),
                }
            )
        document = {"version": self.format_version, "objects": records}
        Path(path).write_text(json.dumps(document, indent=2), encoding="utf-8")

    def load(self, path: str | Path) -> list[Any]:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
        self._validate_document(document)
        objects = []
        records_by_guid = {}
        for record in document.get("objects", []):
            value = self.registry.create(record["type"], record)
            value.guid = record["guid"]
            value.name = record["name"]
            value.metadata = dict(record.get("metadata", {}))
            block_object = getattr(value, "block_object", None)
            if block_object is not None and record.get("block_guid") is not None:
                block_object.guid = record["block_guid"]
            objects.append(value)
            records_by_guid[value.guid] = record
        objects_by_block_guid = {
            value.block_object.guid: value
            for value in objects
            if getattr(value, "block_object", None) is not None
        }
        for value in objects:
            block_object = getattr(value, "block_object", None)
            if block_object is None:
                continue
            record = records_by_guid[value.guid]
            for child_guid in record.get("block_child_guids", []):
                try:
                    child = objects_by_block_guid[child_guid]
                except KeyError as error:
                    raise ValueError(f"Unknown block child GUID: {child_guid}") from error
                child_block = getattr(child, "block_object", None)
                if child_block is None:
                    raise ValueError(f"Object {child_guid} has no block object")
                block_object.add_child_block_object(child_block)
        return objects

    def load_into_project(self, path: str | Path, project) -> list[Any]:
        """Load validated objects into a Project in registration/link phases."""
        objects = self.load(path)
        existing_object_uids = {value.guid for value in project.objects.values()}
        existing_block_uids = {value.guid for value in project.blocks.values()}
        loaded_object_uids = {value.guid for value in objects}
        loaded_block_uids = {
            value.block_object.guid
            for value in objects
            if getattr(value, "block_object", None) is not None
        }
        if existing_object_uids & loaded_object_uids:
            raise ValueError("Loaded object UID already exists in project")
        if existing_block_uids & loaded_block_uids:
            raise ValueError("Loaded block UID already exists in project")
        for value in objects:
            project.add_object(value)
        try:
            for value in objects:
                block_object = getattr(value, "block_object", None)
                if block_object is None:
                    continue
                for child in block_object.child_block_objects:
                    project.connect_blocks(block_object.guid, child.guid)
        except Exception:
            for value in reversed(objects):
                project.remove_object(value.guid)
            raise
        return objects

    def _validate_document(self, document: Any) -> None:
        if not isinstance(document, dict):
            raise ValueError("Project document must be an object")
        if document.get("version") != self.format_version:
            raise ValueError(f"Unsupported project format: {document.get('version')}")
        records = document.get("objects")
        if not isinstance(records, list):
            raise ValueError("Project document objects must be a list")
        object_uids = set()
        block_uids = set()
        for record in records:
            if not isinstance(record, dict):
                raise ValueError("Project object records must be objects")
            for field in ("type", "guid", "name"):
                if not isinstance(record.get(field), str) or not record[field]:
                    raise ValueError(f"Project record requires a non-empty {field}")
            if record["guid"] in object_uids:
                raise ValueError(f"Duplicate serialized object UID: {record['guid']}")
            object_uids.add(record["guid"])
            block_guid = record.get("block_guid")
            if block_guid is not None:
                if not isinstance(block_guid, str) or not block_guid:
                    raise ValueError("Serialized block_guid must be a non-empty string")
                if block_guid in block_uids:
                    raise ValueError(f"Duplicate serialized block UID: {block_guid}")
                block_uids.add(block_guid)
