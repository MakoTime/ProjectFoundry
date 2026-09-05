"""Framework-neutral editor workflow controller."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class EditorController:
    """Open an editor factory and return its accepted model."""

    def __init__(self, factory) -> None:
        self.factory = factory

    def open(
        self,
        parent=None,
        *,
        on_accept: Callable[[Any], Any] | None = None,
        **target,
    ):
        dialog, model = self.factory.create(parent, **target)
        try:
            if dialog.exec() != dialog.DialogCode.Accepted:
                return None
            return on_accept(model) if on_accept is not None else model
        finally:
            dialog.deleteLater()
