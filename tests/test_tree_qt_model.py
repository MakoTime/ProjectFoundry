from PySide6.QtWidgets import QApplication

from projectfoundry.core import ObjectBase
from projectfoundry.tree import TreeNode
from projectfoundry.tree.qt_model import TreeModel

app = QApplication.instance() or QApplication([])


def test_tree_model_exposes_hierarchy_and_unique_names():
    first = ObjectBase("Object")
    second = ObjectBase("Object 001")
    first_node = TreeNode(first.name, node_object=first)
    second_node = TreeNode(second.name, node_object=second)
    first_node.add_child(second_node)
    model = TreeModel([first_node])

    root_index = model.index(0, 0)
    child_index = model.index(0, 0, root_index)

    assert model.data(root_index) == "Object"
    assert model.parent(child_index) == root_index
    assert model.next_name("Object") == "Object 002"


def test_tree_model_rejects_duplicate_edit():
    first = ObjectBase("First")
    second = ObjectBase("Second")
    nodes = [TreeNode(first.name, node_object=first), TreeNode(second.name, node_object=second)]
    model = TreeModel(nodes)

    assert not model.setData(model.index(1, 0), "First")
    assert second.name == "Second"
