"""Base dialog contracts."""

from .editor.button_box import EditorButtonBoxImplementation
from .editor.dialog import DialogEditorFactory, DialogEditorModel, DialogEditorView
from .editor.factory import EditorFactory
from .editor.mixins import EditorApplyMixin, EditorButtonsMixin, EditorCloseMixin, EditorNamingMixin
from .editor.model import EditorModel
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
	"EditorFactory",
	"EditorModel",
	"EditorNamingMixin",
	"EditorView",
	"HasEditorButtons",
	"PopupEditorView",
	"TabEditorFactory",
	"TabEditorModel",
	"TabEditorView",
]
