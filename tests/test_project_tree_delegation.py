from projectfoundry.core import Project
from projectfoundry.tree import TreeNode


def test_attached_node_add_child_registers_through_project():
    project = Project()
    parent = TreeNode("Parent")
    child = TreeNode("Child")
    project.add_node(parent)

    parent.add_child(child)

    assert project.nodes.get(child.guid) is child
    assert child.parent_uid == parent.guid
    assert parent.child_uids == [child.guid]
    assert parent.children == [child]


def test_attached_node_removal_cleans_project_registry():
    project = Project()
    parent = TreeNode("Parent")
    child = TreeNode("Child")
    project.add_node(parent)
    parent.add_child(child)

    assert parent.remove_child(child)

    assert not project.nodes.contains(child.guid)
    assert parent.child_uids == []
    assert parent.children == []
