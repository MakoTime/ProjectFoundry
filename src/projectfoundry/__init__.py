"""Reusable PySide6 and PyVista application foundations."""

from .core import (
	ArtifactMetadata,
	ArtifactStore,
	BlockData,
	BlockObject,
	EditedObject,
	Project,
	ProjectError,
	ProjectEvent,
	ProjectEventKind,
	ProjectManager,
	ProjectSerializer,
	SerializerRegistry,
	TypeRegistry,
	UIDRef,
	UIDRegistry,
	ZipArtifactStore,
)
from .project_app import (
	ProjectContext,
	ProjectLauncherFactory,
	ProjectLauncherModel,
	ProjectLauncherView,
	ProjectPackage,
	ProjectService,
	RecentProject,
	RecentProjectStore,
)
from .scene import PyVistaSceneAdapter, SceneModel
from .scene_table import RowData, SceneObject, SceneTableManager, SceneTableModel, TableManager
from .scripts.install_instructions import update_instructions
from .task_runner import QtTaskRunner, Task, TaskModel, TaskRunner, TaskStatus
from .tree import TreeManager, TreeModel, TreeNode

__version__ = "0.3.0"

__all__ = [
	"BlockObject",
	"BlockData",
	"ArtifactMetadata",
	"ArtifactStore",
	"ZipArtifactStore",
	"EditedObject",
	"ProjectContext",
	"ProjectPackage",
	"ProjectLauncherFactory",
	"ProjectLauncherModel",
	"ProjectLauncherView",
	"RecentProject",
	"RecentProjectStore",
	"ProjectService",
	"Project",
	"ProjectError",
	"ProjectEvent",
	"ProjectEventKind",
	"ProjectManager",
	"ProjectSerializer",
	"PyVistaSceneAdapter",
	"RowData",
	"SceneTableModel",
	"SceneObject",
	"SceneTableManager",
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
