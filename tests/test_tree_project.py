from projectfoundry.core import ObjectBase, Project
from projectfoundry.tree import TreeManager, TreeModel, TreeNode


def test_project_tree_manager_registers_root_and_child_nodes():
    project = Project()
    root = TreeNode("Root")
    child = TreeNode("Child")
    project.tree.add_root_node(root)
    root.add_child(child)

    assert project.nodes.get(root.guid) is root
    assert project.nodes.get(child.guid) is child
    assert project.tree.get_root_nodes() == (root,)
    assert root.child_uids == [child.guid]


def test_project_tree_model_renames_canonical_object_and_aliases():
    project = Project()
    obj = ObjectBase("Old")
    project.add_object(obj)
    first = TreeNode("Old", node_object=obj)
    second = TreeNode("Alias", node_object=obj)
    project.add_node(first, object_uid=obj.guid)
    project.add_node(second, object_uid=obj.guid)
    model = TreeModel([first, second], project=project)

    assert model.setData(model.index(0, 0), "New")
    assert obj.name == "New"
    assert first.name == "New"
    assert second.name == "New"


def test_standalone_tree_manager_remains_constructible():
    manager = TreeManager()
    node = TreeNode("Root")

    manager.add_root_node(node)

    assert manager.get_root_nodes() == (node,)
