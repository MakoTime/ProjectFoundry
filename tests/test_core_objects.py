from projectfoundry.core import (
    BlockData,
    BlockObject,
    EditedObject,
    ProjectSerializer,
    SerializerRegistry,
    TypeRegistry,
)


class ExampleBlock(BlockObject):
    def prepare(self):
        return None

    def process(self, prepared, progress_callback=None):
        return prepared

    def serialise(self, path):
        del path


class ExampleBlockData(BlockData):
    label: str


def test_object_keeps_identity_and_forwards_block_changes():
    block = ExampleBlock("block")
    obj = EditedObject("object", block_object=block)
    changes = []
    obj.add_change_callback(changes.append)

    block.mark_changed()

    assert obj.guid
    assert changes == [obj]


def test_registry_rejects_conflicting_types():
    registry = TypeRegistry()
    registry.register("example", ExampleBlock)

    assert registry.get("example") is ExampleBlock
    try:
        registry.register("example", EditedObject)
    except ValueError:
        pass
    else:
        raise AssertionError("Conflicting registrations must fail")


def test_temporary_object_loads_and_applies_block_data():
    block = ExampleBlock("Block", block_data=ExampleBlockData(label="before"))
    edited = EditedObject.from_block_data(block)
    edited.block_data.label = "after"

    edited.apply_to_block(block)
    edited.destroy()

    assert block.block_data.label == "after"
    assert not block.is_destroyed()


def test_temporary_object_cannot_be_serialized(tmp_path):
    block = ExampleBlock("Block")
    edited = EditedObject.from_block_data(block)

    try:
        ProjectSerializer(SerializerRegistry()).save([edited], tmp_path / "object.json")
    except ValueError as error:
        assert "Temporary objects" in str(error)
    else:
        raise AssertionError("Temporary objects must not be serialized")
