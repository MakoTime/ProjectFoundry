from projectfoundry.core import BlockObject, ObjectBase, ProjectSerializer, SerializerRegistry


class ExampleObject(ObjectBase):
    type_name = "example"


class ExampleBlock(BlockObject):
    def prepare(self):
        return None

    def process(self, prepared, progress_callback=None):
        return prepared

    def serialise(self, path):
        del path


def test_project_serializer_round_trips_registered_objects(tmp_path):
    registry = SerializerRegistry()
    registry.register(
        ExampleObject.type_name,
        lambda record: ExampleObject(record["name"], metadata=record.get("payload", {})),
        lambda value: {"label": value.metadata["label"]},
    )
    serializer = ProjectSerializer(registry)
    original = ExampleObject("Object", metadata={"label": "demo"})
    path = tmp_path / "project.json"

    serializer.save([original], path)
    restored = serializer.load(path)[0]

    assert restored.guid == original.guid
    assert restored.name == original.name
    assert restored.metadata == original.metadata
    assert restored.metadata["label"] == "demo"


def test_project_serializer_rejects_unknown_versions(tmp_path):
    path = tmp_path / "project.json"
    path.write_text('{"version": 999, "objects": []}', encoding="utf-8")
    serializer = ProjectSerializer(SerializerRegistry())

    try:
        serializer.load(path)
    except ValueError as error:
        assert "Unsupported project format" in str(error)
    else:
        raise AssertionError("Unknown format versions must fail")


def test_project_serializer_restores_block_relationships(tmp_path):
    registry = SerializerRegistry()
    registry.register(
        ExampleObject.type_name,
        lambda record: ExampleObject(
            record["name"],
            metadata=record.get("payload", {}),
            block_object=ExampleBlock(record["name"]),
        ),
    )
    serializer = ProjectSerializer(registry)
    child = ExampleObject("Child", block_object=ExampleBlock("Child"))
    parent = ExampleObject("Parent", block_object=ExampleBlock("Parent"))
    parent.block_object.add_child_block_object(child.block_object)
    path = tmp_path / "relationships.json"

    serializer.save([parent, child], path)
    restored = serializer.load(path)
    restored_parent, restored_child = restored

    assert restored_parent.block_object.child_block_objects == (restored_child.block_object,)
