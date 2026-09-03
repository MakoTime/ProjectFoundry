"""Workspace tab editor view."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..view import EditorView


class TabEditorView(EditorView, QWidget):
    """Present a TabEditorModel as a workspace QWidget."""

    def __init__(
        self,
        model=None,
        on_apply: Callable[[Any], Any] | None = None,
        on_close: Callable[[Any, str], Any] | None = None,
        parent=None,
    ) -> None:
        QWidget.__init__(self, parent)
        EditorView.__init__(self, model, on_apply, on_close)
        self._layout = QVBoxLayout(self)
