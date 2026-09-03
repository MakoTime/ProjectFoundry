"""Factory/model/view editor implementation."""

from .button_box import EditorButtonBoxImplementation
from .dialog import DialogEditorFactory, DialogEditorModel, DialogEditorView
from .factory import EditorFactory
from .mixins import EditorApplyMixin, EditorButtonsMixin, EditorCloseMixin, EditorNamingMixin
from .model import EditorModel
from .protocols import HasEditorButtons
from .tab import TabEditorFactory, TabEditorModel, TabEditorView
from .view import EditorView

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
