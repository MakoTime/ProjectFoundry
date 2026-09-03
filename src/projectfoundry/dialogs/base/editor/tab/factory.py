"""Factory for workspace tab editors."""

from __future__ import annotations

from .model import TabEditorModel
from .view import TabEditorView


class TabEditorFactory:
    """Create a TabEditorView for a workspace tab editor model."""

    @staticmethod
    def create(model: TabEditorModel, *, on_apply=None, on_close=None, parent=None):
        return TabEditorView(model, on_apply, on_close, parent)
