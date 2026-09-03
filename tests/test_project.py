import pytest

from projectfoundry.core import BlockObject, ObjectBase, Project, ProjectError, UIDRef
from projectfoundry.tree import TreeNode


class ExampleBlock(BlockObject):
    def prepare(self):
        return None

    def process(self, prepared, progress_callback=None):
        return prepared

    def serialise(self, path):
        del path


def test_project_registers_objects_blocks_and_nodes_by_uid():
    project = Project()
    block = ExampleBlock("Block")
    obj = ObjectBase("Object", block_object=block)
    node = TreeNode("Object", node_object=obj)

    block_ref = project.add_block(block)
    object_ref = project.add_object(obj, block_uid=block_ref.uid)
    node_ref = project.add_node(node, object_uid=object_ref.uid)

    assert isinstance(block_ref, UIDRef)
    assert project.blocks.get(block_ref.uid) is block
    assert project.objects.get(object_ref.uid) is obj
    assert project.nodes.get(node_ref.uid) is node
    assert node.object_uid == obj.guid


def test_project_rejects_duplicate_uids_and_cross_project_items():
    first = Project()
    second = Project()
    block = ExampleBlock("Block")
    first.add_block(block)

    with pytest.raises(ProjectError, match="Duplicate block UID"):
        first.add_block(ExampleBlock("Other", guid=block.guid))
    with pytest.raises(ProjectError, match="another project"):
        second.add_block(block)


def test_project_connects_blocks_using_uid_relationships():
    project = Project()
    parent = ExampleBlock("Parent")
    child = ExampleBlock("Child")
    project.add_block(parent)
    project.add_block(child)

    reference = project.connect_blocks(parent.guid, child.guid, dependent=True)

    assert reference == UIDRef(child.guid)
    assert project.block_child_uids(parent.guid) == (child.guid,)
    assert project._block_parents[child.guid] == [parent.guid]
    assert project._block_dependencies[(parent.guid, child.guid)] is True


def test_project_rejects_cycles_before_mutating_relationships():
    project = Project()
    first = ExampleBlock("First")
    second = ExampleBlock("Second")
    third = ExampleBlock("Third")
    for block in (first, second, third):
        project.add_block(block)
    project.connect_blocks(first.guid, second.guid)
    project.connect_blocks(second.guid, third.guid)

    with pytest.raises(ProjectError, match="cycle"):
        project.connect_blocks(third.guid, first.guid)

    assert project.block_child_uids(third.guid) == ()
    assert project.block_child_uids(first.guid) == (second.guid,)


def test_project_rejects_missing_relationships_without_mutation():
    project = Project()
    parent = ExampleBlock("Parent")
    project.add_block(parent)

    with pytest.raises(ProjectError, match="Unknown block UID"):
        project.connect_blocks(parent.guid, "missing")

    assert project.block_child_uids(parent.guid) == ()


def test_project_scene_membership_and_selection_are_uid_only():
    project = Project()
    obj = ObjectBase("Object")
    project.add_object(obj)

    project.add_to_scene(obj.guid)
    selected = project.select_object(obj.guid)

    assert project.scene_object_uids == [obj.guid]
    assert selected == UIDRef(obj.guid)
    assert project.selected_object_uid == obj.guid
    assert project.remove_from_scene(obj.guid)
    assert project.selected_object_uid is None


def test_project_removes_object_and_all_owned_relationships():
    project = Project()
    block = ExampleBlock("Block")
    obj = ObjectBase("Object")
    node = TreeNode("Object", node_object=obj)
    project.add_block(block)
    project.add_object(obj, block_uid=block.guid)
    project.add_node(node, object_uid=obj.guid)
    project.add_to_scene(obj.guid)

    removed = project.remove_object(obj.guid)

    assert removed is obj
    assert not project.objects.contains(obj.guid)
    assert not project.blocks.contains(block.guid)
    assert not project.nodes.contains(node.guid)
    assert project.scene_object_uids == []


def test_project_removes_nested_nodes_by_uid():
    project = Project()
    root = TreeNode("Root")
    child = TreeNode("Child")
    project.add_node(root)
    project.add_node(child, parent_uid=root.guid)

    project.remove_node(root.guid)

    assert not project.nodes.contains(root.guid)
    assert not project.nodes.contains(child.guid)
    assert project.tree.get_root_nodes() == ()
