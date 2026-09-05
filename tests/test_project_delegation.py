import pytest

from projectfoundry.core import BlockObject, EditedObject, Project, UIDRef
from projectfoundry.dialogs import BlockEditorModel
from projectfoundry.project_app import ProjectService
from projectfoundry.scene_table import SceneTableManager
from projectfoundry.tree import TreeNode


class ExampleBlock(BlockObject):
    def prepare(self):
        return None

    def process(self, prepared, progress_callback=None):
        return prepared

    def serialise(self, path):
        del path


def test_attached_block_adds_child_through_project_and_returns_uid_ref():
    project = Project()
    parent = ExampleBlock("Parent")
    project.add_block(parent)
    child = ExampleBlock("Child")

    reference = parent.add_child_block_object(child, dependent=True)

    assert isinstance(reference, UIDRef)
    assert reference.uid == child.guid
    assert project.blocks.get(child.guid) is child
    assert project.block_child_uids(parent.guid) == (child.guid,)


def test_object_add_to_project_registers_owned_block():
    project = Project()
    SceneTableManager(project)
    block = ExampleBlock("Block")
    obj = EditedObject("Object", block_object=block)

    obj.add_to_project(project)
    obj.add_to_scene()

    assert project.objects.get(obj.guid) is obj
    assert project.blocks.get(block.guid) is block
    assert project.scene_table_manager.scene_block_uids == [block.guid]
    assert obj.project is project


def test_project_aware_object_operations_require_attachment():
    obj = EditedObject("Object")

    with pytest.raises(RuntimeError, match="not attached"):
        obj.add_to_scene()


def test_project_service_delegates_project_owned_operations():
    project = Project()
    service = ProjectService(project)
    block = ExampleBlock("Block")
    node = TreeNode("Block")
    project.add_node(TreeNode("Root"), parent_uid=None)
    root_uid = project.tree.get_root_nodes()[0].guid

    reference = service.add_block_with_node(block, node, parent_uid=root_uid)
    service.rename_block(reference.uid, "Renamed")

    assert service.resolve_block(node.guid) is block
    assert node.name == "Renamed"


def test_editor_block_target_resolves_block_and_node_uids():
    project = Project()
    block = ExampleBlock("Block")
    project.add_block(block)
    node = TreeNode("Block")
    project.add_node(node, object_uid=block.guid)
    scene_object = SceneTableManager(project).add_block(block.guid)

    direct_target = BlockEditorModel(project=project, block_uid=block.guid)
    node_target = BlockEditorModel(project=project, node_uid=node.guid)
    scene_target = BlockEditorModel(project=project, scene_uid=scene_object.scene_uid)

    assert direct_target.resolve_target_block() is block
    assert node_target.resolve_target_block() is block
    assert scene_target.resolve_target_block() is block


def test_editor_block_target_allows_create_mode_and_requires_project_for_uid():
    assert BlockEditorModel().resolve_target_block() is None

    target = BlockEditorModel(block_uid="missing")
    with pytest.raises(RuntimeError, match="project is required"):
        target.resolve_target_block()


def test_editor_block_target_rejects_inconsistent_context_uids():
    project = Project()
    first = ExampleBlock("First")
    second = ExampleBlock("Second")
    project.add_block(first)
    project.add_block(second)
    node = TreeNode("Second")
    project.add_node(node, object_uid=second.guid)

    target = BlockEditorModel(
        project=project,
        block_uid=first.guid,
        node_uid=node.guid,
    )
    with pytest.raises(ValueError, match="must identify one block"):
        target.resolve_target_block()
