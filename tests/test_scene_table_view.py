from projectfoundry.scene_table import TableManager
from projectfoundry.view_templates.scene_table import SceneTableView, SceneTableViewFactory


def test_scene_table_view_factory_configures_model():
    manager = TableManager()
    view = SceneTableViewFactory.create(manager)

    assert isinstance(view, SceneTableView)
    assert view.model().rowCount() == 0
    assert view.selectionBehavior() == view.SelectionBehavior.SelectRows
