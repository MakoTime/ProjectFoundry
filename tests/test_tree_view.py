from projectfoundry.core import EditedObject
from projectfoundry.tree import TreeNode
from projectfoundry.view_templates.tree import TreeView, TreeViewFactory


def test_tree_view_factory_selects_nodes():
    obj = EditedObject("Object")
    node = TreeNode("Object", node_object=obj)
    view = TreeViewFactory.create([node])

    view.select_node(node)

    assert isinstance(view, TreeView)
    assert view.selected_node() is node
    view.close()
