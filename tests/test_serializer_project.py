import json

import pytest

from projectfoundry.core import (
    BlockObject,
    ObjectBase,
    Project,
    ProjectSerializer,
    SerializerRegistry,
)


class ExampleBlock(BlockObject):
    def prepare(self):
        return None

    def process(self, prepared, progress_callback=None):
        return prepared

    def serialise(self, path):
        del path


class ExampleObject(ObjectBase):
    type_name = "example-project"


def registry():
    result = SerializerRegistry()
    result.register(
        ExampleObject.type_name,
        lambda record: ExampleObject(
            record["name"],
            block_object=ExampleBlock(record["name"]),
            metadata=record.get("payload", {}),
        ),
    )
    return result


def test_load_into_project_restores_objects_and_project_block_edges(tmp_path):
    serializer = ProjectSerializer(registry())
    original = Project()
    child = ExampleObject("Child", block_object=ExampleBlock("Child"))
    parent = ExampleObject("Parent", block_object=ExampleBlock("Parent"))
    original.add_object(child)
    original.add_object(parent)
    parent.block_object.add_child_block_object(child.block_object)
    path = tmp_path / "project.json"
    serializer.save_project(original, path)

    restored_project = Project()
    restored = serializer.load_into_project(path, restored_project)
    restored_parent = next(value for value in restored if value.name == "Parent")
    restored_child = next(value for value in restored if value.name == "Child")

    assert restored_project.objects.get(restored_parent.guid) is restored_parent
    assert restored_project.block_child_uids(restored_parent.block_object.guid) == (
        restored_child.block_object.guid,
    )


def test_load_rejects_duplicate_serialized_object_uids(tmp_path):
    value = {
        "version": 1,
        "objects": [
            {"type": "x", "guid": "same", "name": "a"},
            {"type": "x", "guid": "same", "name": "b"},
        ],
    }
    path = tmp_path / "duplicate.json"
    path.write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(ValueError, match="Duplicate serialized object UID"):
        ProjectSerializer(registry()).load(path)


def test_load_into_project_preflights_existing_uid_without_mutation(tmp_path):
    project = Project()
    existing = ExampleObject("Existing")
    project.add_object(existing)
    value = {
        "version": 1,
        "objects": [{"type": ExampleObject.type_name, "guid": existing.guid, "name": "Other"}],
    }
    path = tmp_path / "conflict.json"
    path.write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(ValueError, match="already exists"):
        ProjectSerializer(registry()).load_into_project(path, project)
    assert project.objects.get(existing.guid) is existing
