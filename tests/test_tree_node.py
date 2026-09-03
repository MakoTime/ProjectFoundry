from projectfoundry.tree import TreeManager, TreeNode


def test_tree_nodes_preserve_parent_child_relationships():
    root = TreeNode("root")
    child = TreeNode("child")
    root.add_child(child)

    assert child.parent is root
    assert root.children == [child]
    assert root.remove_child(child)
    assert child.parent is None


def test_tree_manager_removes_all_alias_nodes_for_object():
    manager = TreeManager()
    obj = object()
    first = TreeNode("first", node_object=obj)
    second = TreeNode("second", node_object=obj)
    root = TreeNode("root")
    root.add_child(first)
    root.add_child(second)
    manager.add_root_node(root)

    assert manager.remove_object(obj)
    assert root.children == []
