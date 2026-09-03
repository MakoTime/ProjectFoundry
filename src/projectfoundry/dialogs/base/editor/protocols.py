"""Protocols shared by editor presentations."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from PySide6.QtWidgets import QAbstractButton, QDialogButtonBox


@runtime_checkable
class HasEditorButtons(Protocol):
    """Interface for editors exposing standard action buttons."""

    @property
    def ok_button(self) -> QAbstractButton | None: ...

    @property
    def cancel_button(self) -> QAbstractButton | None: ...

    @property
    def apply_button(self) -> QAbstractButton | None: ...

    def create_button_box(
        self,
        buttons: QDialogButtonBox.StandardButton | None = None,
    ) -> QDialogButtonBox: ...
