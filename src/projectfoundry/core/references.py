"""Stable UID references used by project relationships."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UIDRef:
    """An immutable reference to an item owned by a project registry."""

    uid: str

    def __post_init__(self) -> None:
        if not self.uid:
            raise ValueError("A UID reference requires a non-empty UID")
