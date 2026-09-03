from PySide6.QtCore import Qt

from projectfoundry.tree import TreeDropdownFactory, TreeDropdownModel, TreeNode


def test_dropdown_model_flattens_nodes_and_retains_identity():
    root = TreeNode("Root")
    child = TreeNode("Child")
    root.add_child(child)
    model = TreeDropdownModel([root])

    assert model.rowCount() == 2
    assert model.data(model.index(1, 0), Qt.ItemDataRole.DisplayRole) == "  Child"
    assert model.data(model.index(1, 0), Qt.ItemDataRole.UserRole) is child


def test_dropdown_factory_wires_model_and_selection():
    node = TreeNode("Object")
    view = TreeDropdownFactory.create([node])
    view.set_selected_node(node)

    assert view.selected_node() is node
