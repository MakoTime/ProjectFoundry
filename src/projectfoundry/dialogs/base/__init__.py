"""Base dialog contracts."""

from .editor.button_box import EditorButtonBoxImplementation
from .editor.controller import EditorController
from .editor.dialog import DialogEditorFactory, DialogEditorModel, DialogEditorView
from .editor.factory import EditorFactory
from .editor.mixins import (
	EditorApplyMixin,
	EditorButtonsMixin,
	EditorCloseMixin,
	EditorNameMixin,
	EditorNamingMixin,
)
from .editor.model import BlockEditorModel, EditorModel
from .editor.protocols import HasEditorButtons
from .editor.tab import TabEditorFactory, TabEditorModel, TabEditorView
from .editor.view import EditorView

PopupEditorView = DialogEditorView

__all__ = [
	"DialogEditorFactory",
	"DialogEditorModel",
	"DialogEditorView",
	"EditorApplyMixin",
	"EditorButtonBoxImplementation",
	"EditorButtonsMixin",
	"EditorCloseMixin",
	"EditorController",
	"EditorFactory",
	"EditorModel",
	"EditorNamingMixin",
	"EditorNameMixin",
	"EditorView",
	"BlockEditorModel",
	"HasEditorButtons",
	"PopupEditorView",
	"TabEditorFactory",
	"TabEditorModel",
	"TabEditorView",
]
