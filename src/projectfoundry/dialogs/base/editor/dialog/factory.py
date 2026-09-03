"""Factory for modal dialog editors."""

from __future__ import annotations

from .model import DialogEditorModel
from .view import DialogEditorView


class DialogEditorFactory:
    """Create a DialogEditorView for a dialog editor model."""

    @staticmethod
    def create(model: DialogEditorModel, *, on_apply=None, on_close=None, parent=None):
        return DialogEditorView(model, on_apply, on_close, parent)
