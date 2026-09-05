from PySide6.QtWidgets import QDialogButtonBox, QTabWidget

from projectfoundry.dialogs.base import (
    DialogEditorFactory,
    DialogEditorModel,
    DialogEditorView,
    EditorController,
    EditorFactory,
    EditorModel,
    EditorView,
    PopupEditorView,
    TabEditorFactory,
    TabEditorModel,
    TabEditorView,
)


class ExampleModel(EditorModel):
    def __init__(self):
        self.applied = False

    def apply(self):
        self.applied = True
        return self


class ExampleDialogModel(DialogEditorModel):
    pass


class ExampleTabModel(TabEditorModel):
    pass


def test_editor_controller_returns_accepted_model_and_cleans_up():
    class Dialog:
        DialogCode = type("DialogCode", (), {"Accepted": 1})

        def __init__(self, result):
            self.result = result
            self.deleted = False

        def exec(self):
            return self.result

        def deleteLater(self):
            self.deleted = True

    dialog = Dialog(1)
    model = ExampleModel()

    class Factory:
        @staticmethod
        def create(parent, **target):
            del parent, target
            return dialog, model

    assert EditorController(Factory).open() is model
    assert dialog.deleted


def test_editor_controller_returns_none_when_cancelled():
    class Dialog:
        DialogCode = type("DialogCode", (), {"Accepted": 1})

        def exec(self):
            return 0

        def deleteLater(self):
            self.deleted = True

    dialog = Dialog()

    class Factory:
        @staticmethod
        def create(parent, **target):
            del parent, target
            return dialog, ExampleModel()

    assert EditorController(Factory).open() is None
    assert dialog.deleted


def test_popup_editor_applies_model_and_notifies_once():
    model = ExampleModel()
    applied = []
    closed = []
    view = EditorFactory.create(
        model,
        mode="popup",
        on_apply=applied.append,
        on_close=lambda value, reason: closed.append((value, reason)),
    )
    buttons = view.create_button_box()

    buttons.button(QDialogButtonBox.StandardButton.Ok).click()
    view.reject()

    assert isinstance(view, PopupEditorView)
    assert model.applied
    assert applied == [model]
    assert closed == [(model, "ok")]


def test_tab_editor_can_be_added_to_workspace_tabs():
    model = ExampleModel()
    view = EditorFactory.create(model, mode="tab")
    assert isinstance(view, TabEditorView)
    view.create_button_box()
    tabs = QTabWidget()
    tabs.addTab(view, "Editor")

    view.apply_button.click()

    assert model.applied
    assert tabs.count() == 1
    view.close()


def test_dedicated_editor_types_inherit_shared_contracts():
    dialog_model = ExampleDialogModel()
    tab_model = ExampleTabModel()
    dialog_view = DialogEditorFactory.create(dialog_model)
    tab_view = TabEditorFactory.create(tab_model)

    assert isinstance(dialog_model, EditorModel)
    assert isinstance(tab_model, EditorModel)
    assert isinstance(dialog_view, DialogEditorView)
    assert isinstance(tab_view, TabEditorView)
    assert isinstance(dialog_view, EditorView)
    assert isinstance(tab_view, EditorView)
    assert isinstance(EditorFactory.create(dialog_model), DialogEditorView)
    assert isinstance(EditorFactory.create(tab_model, mode="tab"), TabEditorView)
    dialog_view.close()
    tab_view.close()
