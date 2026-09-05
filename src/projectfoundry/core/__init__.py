"""Framework-neutral project and processing primitives."""

from .artifacts import ArtifactStore, ZipArtifactStore
from .block_object import ArtifactMetadata, BlockData, BlockObject
from .object import EditedObject
from .project import Project, ProjectError, ProjectEvent, ProjectEventKind, UIDRegistry
from .project_manager import ProjectManager
from .references import UIDRef
from .registry import TypeRegistry
from .serialization import ProjectSerializer, SerializerRegistry

__all__ = [
	"BlockObject",
	"ArtifactStore",
	"ZipArtifactStore",
	"BlockData",
	"ArtifactMetadata",
	"EditedObject",
	"ProjectSerializer",
	"Project",
	"ProjectError",
	"ProjectEvent",
	"ProjectEventKind",
	"ProjectManager",
	"SerializerRegistry",
	"TypeRegistry",
	"UIDRef",
	"UIDRegistry",
]
