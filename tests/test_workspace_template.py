from PySide6.QtWidgets import QWidget

from projectfoundry.tree import TreeNode
from projectfoundry.view_templates.workspace import MainWindowTemplate, MainWindowTemplateFactory


class Plotter:
    def __init__(self):
        self.interactor = QWidget()

    def set_background(self, color):
        del color

    def show_axes(self):
        pass


def test_workspace_template_composes_project_views():
    root = TreeNode("Root")
    window = MainWindowTemplateFactory.create([root], plotter=Plotter())

    assert isinstance(window, MainWindowTemplate)
    assert window.tree_view.model() is window.tree_model
    assert window.scene_table_view.model() is window.scene_table_model
    assert window.scene_view.scene_model is window.scene_model
    window.close()
