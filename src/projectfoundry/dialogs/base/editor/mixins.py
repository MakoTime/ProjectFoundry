"""Composable editor workflow mixins."""

from __future__ import annotations

from collections.abc import Iterable

from PySide6.QtWidgets import QDialogButtonBox, QLineEdit

from .button_box import EditorButtonBoxImplementation


class EditorNameMixin:
    """Provide a shared name field for views editing named models."""

    def create_name_editor(self) -> QLineEdit:
        self.name_edit = QLineEdit(self)
        self.name_edit.setText(str(getattr(self.model, "name", "")))
        return self.name_edit

    def update_model(self):
        self.model.name = self.name_edit.text()
        return super().update_model()


class EditorApplyMixin:
    """Apply the view's current values through its model."""

    def update_model(self):
        return self.model

    def apply_model(self):
        if self.model is None:
            return None
        return self.model.apply()

    def apply_changes(self):
        self.update_model()
        result = self.apply_model()
        if self._on_apply is not None:
            self._on_apply(result)
        return result


class EditorCloseMixin:
    """Publish one close notification for any editor presentation."""

    def notify_closed(self, reason: str = "window") -> bool:
        if self._close_notified:
            return False
        self._close_notified = True
        if self._on_close is not None:
            self._on_close(self.model, reason)
        return True

    def closeEvent(self, event) -> None:
        self.notify_closed()
        super().closeEvent(event)


class EditorButtonsMixin(EditorButtonBoxImplementation):
    """Create standard buttons and route their actions to the host widget."""

    def create_button_box(
        self,
        buttons: QDialogButtonBox.StandardButton | None = None,
    ) -> QDialogButtonBox:
        if buttons is None:
            buttons = (
                QDialogButtonBox.StandardButton.Ok
                | QDialogButtonBox.StandardButton.Cancel
                | QDialogButtonBox.StandardButton.Apply
            )
        if self.button_box is None:
            self.button_box = QDialogButtonBox(buttons, parent=self)
            self.button_box.accepted.connect(self._apply_and_accept)
            self.button_box.rejected.connect(self._reject_editor)
            self.button_box.clicked.connect(self._handle_button)
            self._layout.addWidget(self.button_box)
        return self.button_box

    def _handle_button(self, button) -> None:
        if self.button_box is not None:
            standard_button = self.button_box.standardButton(button)
            if standard_button == QDialogButtonBox.StandardButton.Apply:
                self.apply_changes()


class EditorNamingMixin:
    """Provide deterministic unique names from a supplied name source."""

    def next_available_name(self, existing_names: Iterable[str] | None = None) -> str:
        prefix = str(getattr(self.model, "name", "Undefined")).strip() or "Undefined"
        names = {str(name) for name in (existing_names or ())}
        if prefix not in names:
            return prefix
        index = 1
        while f"{prefix} {index:03d}" in names:
            index += 1
        return f"{prefix} {index:03d}"
