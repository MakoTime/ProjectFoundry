import json

import pytest

from projectfoundry.core import (
    BlockData,
    BlockObject,
    EditedObject,
    Project,
    ProjectSerializer,
    SerializerRegistry,
)


class ExampleBlock(BlockObject):
    type_name = "example_block"

    def prepare(self):
        return None

    def process(self, prepared, progress_callback=None):
        return prepared

    def serialise(self, path):
        del path


class ExampleBlockData(BlockData):
    label: str


class ExampleObject(EditedObject):
    type_name = "example-project"


def registry():
    result = SerializerRegistry()
    result.register_block(
        ExampleBlock.type_name,
        lambda record: ExampleBlock(record["name"]),
    )
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

    assert restored_project.blocks.get(restored_parent.guid) is restored_parent
    assert restored_project.block_child_uids(restored_parent.guid) == (restored_child.guid,)


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


def test_serializer_round_trips_independent_blocks_and_relationships(tmp_path):
    serializer_registry = SerializerRegistry()
    serializer_registry.register_block(
        ExampleBlock.type_name,
        lambda record: ExampleBlock(
            record["name"],
            block_data=ExampleBlockData(**record["data"]),
        ),
    )
    serializer = ProjectSerializer(serializer_registry)
    project = Project()
    child = ExampleBlock("Child", block_data=ExampleBlockData(label="child"))
    parent = ExampleBlock("Parent", block_data=ExampleBlockData(label="parent"))
    project.add_block(child)
    project.add_block(parent)
    project.connect_blocks(parent.guid, child.guid)
    path = tmp_path / "blocks.json"

    serializer.save_blocks(project, path)
    restored = serializer.load_blocks(path)

    restored_parent = next(block for block in restored if block.name == "Parent")
    restored_child = next(block for block in restored if block.name == "Child")
    assert restored_parent.block_data.label == "parent"
    assert restored_parent.child_block_objects == (restored_child,)


def test_project_state_load_rejects_unknown_scene_block_without_mutation(tmp_path):
    serializer = ProjectSerializer(registry())
    existing = ExampleBlock("Existing")
    project = Project()
    project.add_block(existing)
    value = {
        "version": serializer.format_version,
        "blocks": [],
        "tree": [],
        "scene_table": [{"block_uid": "missing"}],
    }
    path = tmp_path / "invalid-project.json"
    path.write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(ValueError, match="Unknown scene block UID"):
        serializer.load_into_project(path, project)

    assert project.blocks.get(existing.guid) is existing
    assert project.scene_table_manager is None


def test_project_state_restores_scene_presentation_state(tmp_path):
    serializer_registry = SerializerRegistry()
    serializer_registry.register_block(
        ExampleBlock.type_name,
        lambda record: ExampleBlock(record["name"]),
    )
    serializer = ProjectSerializer(serializer_registry)
    project = Project()
    block = ExampleBlock("Object")
    project.add_block(block)
    from projectfoundry.scene_table import SceneTableManager

    manager = SceneTableManager(project)
    scene_object = manager.add_block(block.guid, visible=False, transparency=0.35)
    path = tmp_path / "presentation.json"
    serializer.save_project(project, path)

    restored = Project()
    serializer.load_into_project(path, restored)
    restored_object = restored.scene_table_manager.scene_objects[block.guid]

    assert restored_object.scene_uid == scene_object.scene_uid
    assert restored_object.visible is False
    assert restored_object.transparency == 0.35
