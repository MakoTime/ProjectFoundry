import json
import zipfile

import pytest

from projectfoundry.core import ProjectSerializer, SerializerRegistry
from projectfoundry.project_app import ProjectPackage


def test_package_create_and_extract(tmp_path):
    package = ProjectPackage(".demo")
    package_path = package.create(tmp_path / "example", name="Example")

    working_directory = package.extract(package_path, tmp_path / "workspaces")

    assert package_path == tmp_path / "example.demo"
    assert json.loads((working_directory / "project.json").read_text()) ["blocks"] == []
    assert json.loads((working_directory / "metadata.json").read_text())["name"] == "Example"


def test_package_extract_reuses_stable_working_directory(tmp_path):
    package = ProjectPackage()
    package_path = package.create(tmp_path / "example")
    workspace = tmp_path / "workspaces"

    first = package.extract(package_path, workspace)
    second = package.extract(package_path, workspace)

    assert first == second


def test_package_pack_replaces_existing_package_atomically(tmp_path):
    package = ProjectPackage()
    package_path = package.create(tmp_path / "example")
    working_directory = package.extract(package_path, tmp_path / "workspaces")
    (working_directory / "project.json").write_text('{"changed": true}', encoding="utf-8")

    package.pack(working_directory, package_path)
    restored = package.extract(package_path, tmp_path / "second-workspace")

    assert json.loads((restored / "project.json").read_text())["changed"] is True


def test_package_rejects_unsafe_members(tmp_path):
    path = tmp_path / "unsafe.pfzip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("../escape.txt", "bad")

    with pytest.raises(ValueError, match="Unsafe"):
        ProjectPackage().extract(path, tmp_path / "workspaces")


def test_package_open_context_can_load_project_document(tmp_path):
    package = ProjectPackage()
    package_path = package.create(tmp_path / "example")

    context = package.open_context(package_path, working_root=tmp_path / "workspaces")

    assert context.project.blocks.values() == ()


def test_project_context_save_repackages_working_project(tmp_path):
    package = ProjectPackage()
    package_path = package.create(tmp_path / "example")
    context = package.open_context(package_path, working_root=tmp_path / "workspaces")

    context.save(package, ProjectSerializer(SerializerRegistry()))

    restored = package.extract(package_path, working_root=tmp_path / "restored")
    assert json.loads((restored / "project.json").read_text())["blocks"] == []
    assert context.dirty is False