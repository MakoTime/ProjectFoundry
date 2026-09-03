"""Registries for extensible project object and block types."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class TypeRegistry:
    """Map stable type names to constructors or serializer handlers."""

    def __init__(self) -> None:
        self._types: dict[str, Any] = {}

    def register(self, name: str, value: Any) -> Any:
        if not name:
            raise ValueError("A registry name is required")
        if name in self._types and self._types[name] is not value:
            raise ValueError(f"Type already registered: {name}")
        self._types[name] = value
        return value

    def decorator(self, name: str) -> Callable[[Any], Any]:
        def register_type(value: Any) -> Any:
            return self.register(name, value)

        return register_type

    def get(self, name: str) -> Any:
        try:
            return self._types[name]
        except KeyError as error:
            raise KeyError(f"Unknown registry type: {name}") from error

    def contains(self, name: str) -> bool:
        return name in self._types

    def names(self) -> tuple[str, ...]:
        return tuple(self._types)
