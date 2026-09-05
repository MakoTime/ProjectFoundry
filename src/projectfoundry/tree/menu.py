"""Context menus for tree node actions."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu

from .node import TreeNode


@dataclass
class Option:
    name: str
    icon_str: str | None = None
    tooltip: str | None = None
    enabled: bool = True
    callback: Callable[[], object] | None = None


class TreeNodeMenu(QMenu):
    """Menu exposing actions available for one tree node."""

    def __init__(
        self,
        node: TreeNode,
        options: Iterable[Option] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.node = node
        self.options = list(options) if options is not None else self.default_options(node)
        self.actions_by_name: dict[str, QAction] = {}
        for option in self.options:
            icon = QIcon(option.icon_str) if option.icon_str else QIcon()
            action = self.addAction(icon, option.name)
            action.setToolTip(option.tooltip or "")
            action.setEnabled(option.enabled)
            if option.callback is not None:
                action.triggered.connect(lambda checked=False, callback=option.callback: callback())
            self.actions_by_name[option.name] = action

        self.add_to_scene_action = self.actions_by_name.get("Add to scene")
        self.delete_action = self.actions_by_name.get("Delete")

    @staticmethod
    def default_options(node: TreeNode) -> list[Option]:
        return [
            Option("Add to scene", enabled=node.can_add_to_scene(), callback=node.add_to_scene),
            Option("Delete", enabled=node.can_delete(), callback=node.delete),
        ]


class TreeNodeMenuFactory:
    """Construct a context menu for a tree node."""

    @staticmethod
    def default_options(node: TreeNode) -> list[Option]:
        return TreeNodeMenu.default_options(node)

    @staticmethod
    def create(
        node: TreeNode,
        options: Iterable[Option] | None = None,
        parent=None,
    ) -> TreeNodeMenu:
        return TreeNodeMenu(node, options, parent)