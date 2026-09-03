"""Shared editor view workflow."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .mixins import EditorApplyMixin, EditorButtonsMixin, EditorCloseMixin, EditorNamingMixin


class EditorView(EditorApplyMixin, EditorCloseMixin, EditorButtonsMixin, EditorNamingMixin):
    """Shared non-widget behavior for dialog and tab editor views."""

    def __init__(
        self,
        model=None,
        on_apply: Callable[[Any], Any] | None = None,
        on_close: Callable[[Any, str], Any] | None = None,
    ) -> None:
        self.model = model
        self._on_apply = on_apply
        self._on_close = on_close
        self._close_notified = False
        self.button_box = None

    def _apply_and_accept(self) -> None:
        self.apply_changes()
        self.notify_closed("ok")
        self._accept_editor()

    def _reject_editor(self) -> None:
        self.notify_closed("cancel")
        self._reject_editor_container()

    def _accept_editor(self) -> None:
        self.close()

    def _reject_editor_container(self) -> None:
        self.close()
