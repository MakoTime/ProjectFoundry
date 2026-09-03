"""Modal dialog editor view."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtWidgets import QDialog, QVBoxLayout

from ..view import EditorView


class DialogEditorView(EditorView, QDialog):
    """Present a DialogEditorModel in a modal QDialog."""

    def __init__(
        self,
        model=None,
        on_apply: Callable[[Any], Any] | None = None,
        on_close: Callable[[Any, str], Any] | None = None,
        parent=None,
    ) -> None:
        QDialog.__init__(self, parent)
        EditorView.__init__(self, model, on_apply, on_close)
        self._layout = QVBoxLayout(self)

    def _accept_editor(self) -> None:
        self.accept()

    def _reject_editor_container(self) -> None:
        self.reject()
