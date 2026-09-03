"""Factories for standard editor presentations."""

from __future__ import annotations

from .dialog.factory import DialogEditorFactory
from .tab.factory import TabEditorFactory


class EditorFactory:
    """Compatibility dispatcher for dedicated dialog and tab factories."""

    @staticmethod
    def create(model, *, mode: str = "popup", on_apply=None, on_close=None, parent=None):
        if mode == "popup":
            return DialogEditorFactory.create(
                model,
                on_apply=on_apply,
                on_close=on_close,
                parent=parent,
            )
        if mode == "tab":
            return TabEditorFactory.create(
                model,
                on_apply=on_apply,
                on_close=on_close,
                parent=parent,
            )
        raise ValueError(f"Unknown editor mode: {mode}")
