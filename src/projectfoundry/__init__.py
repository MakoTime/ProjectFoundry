"""Reusable PySide6 and PyVista application foundations."""

from .core import (
	BlockObject,
	ObjectBase,
	Project,
	ProjectError,
	ProjectEvent,
	ProjectManager,
	ProjectSerializer,
	SerializerRegistry,
	TypeRegistry,
	UIDRef,
	UIDRegistry,
)
from .scene import PyVistaSceneAdapter, SceneModel
from .scene_table import RowData, SceneTableModel, TableManager
from .scripts.install_instructions import update_instructions
from .task_runner import QtTaskRunner, Task, TaskModel, TaskRunner, TaskStatus
from .tree import TreeManager, TreeModel, TreeNode

__version__ = "0.1.1"

__all__ = [
	"BlockObject",
	"ObjectBase",
	"Project",
	"ProjectError",
	"ProjectEvent",
	"ProjectManager",
	"ProjectSerializer",
	"PyVistaSceneAdapter",
	"RowData",
	"SceneTableModel",
	"SceneModel",
	"SerializerRegistry",
	"Task",
	"TaskModel",
	"TaskRunner",
	"TaskStatus",
	"TableManager",
	"TreeManager",
	"TreeModel",
	"TreeNode",
	"TypeRegistry",
	"UIDRef",
	"UIDRegistry",
	"QtTaskRunner",
	"update_instructions",
	"__version__",
]
