"""Reusable standard editor button-box behavior."""

from __future__ import annotations

from PySide6.QtWidgets import QDialogButtonBox


class EditorButtonBoxImplementation:
    """Expose standard editor buttons from an assigned button box."""

    button_box: QDialogButtonBox | None = None

    @property
    def ok_button(self):
        return self._button(QDialogButtonBox.StandardButton.Ok)

    @property
    def cancel_button(self):
        return self._button(QDialogButtonBox.StandardButton.Cancel)

    @property
    def apply_button(self):
        return self._button(QDialogButtonBox.StandardButton.Apply)

    def _button(self, standard_button):
        if self.button_box is None:
            return None
        return self.button_box.button(standard_button)
