"""Factory/model/view editor implementation."""

from .button_box import EditorButtonBoxImplementation
from .controller import EditorController
from .dialog import DialogEditorFactory, DialogEditorModel, DialogEditorView
from .factory import EditorFactory
from .mixins import (
	EditorApplyMixin,
	EditorButtonsMixin,
	EditorCloseMixin,
	EditorNameMixin,
	EditorNamingMixin,
)
from .model import BlockEditorModel, EditorModel
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
