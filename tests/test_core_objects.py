from projectfoundry.core import BlockObject, ObjectBase, TypeRegistry


class ExampleBlock(BlockObject):
    def prepare(self):
        return None

    def process(self, prepared, progress_callback=None):
        return prepared

    def serialise(self, path):
        del path


def test_object_keeps_identity_and_forwards_block_changes():
    block = ExampleBlock("block")
    obj = ObjectBase("object", block_object=block)
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
        registry.register("example", ObjectBase)
    except ValueError:
        pass
    else:
        raise AssertionError("Conflicting registrations must fail")
