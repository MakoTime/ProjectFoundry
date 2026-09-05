from PySide6.QtCore import Qt

from projectfoundry.core import BlockObject, Project
from projectfoundry.scene_table import SceneTableManager
from projectfoundry.tree import (
    Option,
    TreeDropdownFactory,
    TreeDropdownModel,
    TreeNode,
)


class ExampleBlock(BlockObject):
    def prepare(self):
        return None

    def process(self, prepared, progress_callback=None):
        return prepared

    def serialise(self, path):
        del path


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


def test_menu_option_describes_a_node_action():
    called = []
    option = Option("Inspect", tooltip="Inspect this node", callback=lambda: called.append(True))

    assert option.name == "Inspect"
    assert option.tooltip == "Inspect this node"
    option.callback()
    assert called == [True]


def test_node_actions_delegate_to_project():
    project = Project()
    block = ExampleBlock("Object")
    project.add_block(block)
    SceneTableManager(project)
    node = TreeNode("Object")
    node.object_uid = block.guid
    project.add_node(node, object_uid=block.guid)

    node.add_to_scene()

    assert project.scene_table_manager.scene_block_uids == [block.guid]
