"""Base model contract for editable dialogs."""

from __future__ import annotations


class EditorModel:
    """Small common contract for models edited by a workspace view."""

    def validate(self) -> None:
        """Raise a domain error when the current model cannot be applied."""
        return None

    def apply(self):
        """Validate and return the applied model value."""
        self.validate()
        return self
