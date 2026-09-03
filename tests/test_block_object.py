from projectfoundry.core import BlockObject


class ExampleBlock(BlockObject):
    def prepare(self):
        return None

    def process(self, prepared, progress_callback=None):
        return prepared

    def serialise(self, path):
        del path


def test_change_invalidates_parents_and_calls_callbacks():
    child = ExampleBlock("child")
    parent = ExampleBlock("parent")
    parent.add_child_block_object(child)
    changes = []
    parent.add_change_callback(changes.append)

    child.mark_changed()

    assert not child.is_valid()
    assert not parent.is_valid()
    assert changes == [parent]


def test_dependent_parent_is_destroyed_with_child():
    child = ExampleBlock("child")
    parent = ExampleBlock("parent")
    parent.add_child_block_object(child, dependent=True)

    child.destroy()

    assert parent.is_destroyed()
    assert child.child_block_objects == ()
