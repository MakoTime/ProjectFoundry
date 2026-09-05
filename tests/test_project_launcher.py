from projectfoundry.project_app import (
    ProjectLauncherModel,
    ProjectPackage,
    RecentProjectStore,
)


def test_launcher_creates_project_context_and_remembers_project(tmp_path):
    package_path = tmp_path / "demo.pfzip"
    model = ProjectLauncherModel(
        ProjectPackage(".pfzip"),
        RecentProjectStore(tmp_path / "recent.json"),
    )

    context = model.create_project(package_path, name="Demo")

    assert context.package_path == package_path
    assert context.working_directory is None
    assert model.recent_projects()[0].name == "Demo"
    assert context.project.artifact_store.archive_path == package_path


def test_launcher_opens_existing_project_and_remembers_file(tmp_path):
    package = ProjectPackage()
    package_path = package.create(tmp_path / "demo", name="Demo")
    model = ProjectLauncherModel(
        package,
        RecentProjectStore(tmp_path / "recent.json"),
    )

    context = model.open_file(package_path)

    assert context.package_path == package_path
    assert model.recent_projects()[0].path == str(package_path.resolve())
