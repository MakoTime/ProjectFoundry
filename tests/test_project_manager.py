from projectfoundry.core import Project, ProjectManager


def test_project_manager_is_singleton_but_projects_are_not():
    ProjectManager.reset_singleton()
    first_manager = ProjectManager()
    second_manager = ProjectManager()
    first_project = Project()
    second_project = Project()

    assert first_manager is second_manager
    assert first_project is not second_project
    assert first_manager.current_project is second_manager.current_project
    ProjectManager.reset_singleton()


def test_project_manager_replaces_active_project_and_notifies():
    ProjectManager.reset_singleton()
    manager = ProjectManager()
    changed = []
    manager.add_project_changed_callback(changed.append)
    replacement = Project()

    result = manager.set_current_project(replacement)

    assert result is replacement
    assert manager.current_project is replacement
    assert changed == [replacement]
    ProjectManager.reset_singleton()


def test_project_manager_new_project_replaces_current():
    ProjectManager.reset_singleton()
    manager = ProjectManager()
    previous = manager.current_project

    replacement = manager.new_project()

    assert replacement is manager.current_project
    assert replacement is not previous
    ProjectManager.reset_singleton()
