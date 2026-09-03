import pytest

from projectfoundry.core import BlockObject, ObjectBase, Project, UIDRef


class ExampleBlock(BlockObject):
    def prepare(self):
        return None

    def process(self, prepared, progress_callback=None):
        return prepared

    def serialise(self, path):
        del path


def test_attached_block_adds_child_through_project_and_returns_uid_ref():
    project = Project()
    parent = ExampleBlock("Parent")
    project.add_block(parent)
    child = ExampleBlock("Child")

    reference = parent.add_child_block_object(child, dependent=True)

    assert isinstance(reference, UIDRef)
    assert reference.uid == child.guid
    assert project.blocks.get(child.guid) is child
    assert project.block_child_uids(parent.guid) == (child.guid,)


def test_object_add_to_project_registers_owned_block():
    project = Project()
    block = ExampleBlock("Block")
    obj = ObjectBase("Object", block_object=block)

    obj.add_to_project(project)
    obj.add_to_scene()

    assert project.objects.get(obj.guid) is obj
    assert project.blocks.get(block.guid) is block
    assert project.scene_object_uids == [obj.guid]
    assert obj.project is project


def test_project_aware_object_operations_require_attachment():
    obj = ObjectBase("Object")

    with pytest.raises(RuntimeError, match="not attached"):
        obj.add_to_scene()
