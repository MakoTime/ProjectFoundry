from PySide6.QtCore import Qt

from projectfoundry.scene_table import (
    CellObject,
    RowData,
    SceneTableModel,
    TableManager,
    VisibleField,
)


def test_scene_table_presents_rows_and_visibility():
    changed = []
    obj = object()
    row = RowData("Object", VisibleField(True, changed.append), CellObject(obj))
    manager = TableManager()
    model = SceneTableModel(manager)
    model.add_row(row)

    index = model.index(0, model.VISIBLE)
    assert model.data(index, Qt.ItemDataRole.CheckStateRole) == Qt.CheckState.Checked
    assert model.setData(index, Qt.CheckState.Unchecked, Qt.ItemDataRole.CheckStateRole)
    assert changed == [False]


def test_scene_table_removes_row_and_notifies_object():
    class SceneObject:
        def __init__(self):
            self.removed = False

        def remove_from_scene(self):
            self.removed = True

    obj = SceneObject()
    row = RowData("Object", VisibleField(True, lambda visible: None), CellObject(obj))
    model = SceneTableModel(TableManager())
    model.add_row(row)

    assert model.remove_row(0)
    assert obj.removed
    assert model.rowCount() == 0
