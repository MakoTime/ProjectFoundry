from projectfoundry.project_app import RecentProjectStore


def test_recent_projects_are_deduplicated_and_ordered(tmp_path):
    store = RecentProjectStore(tmp_path / "recent.json")
    first = tmp_path / "first.pfzip"
    second = tmp_path / "second.pfzip"
    first.touch()
    second.touch()

    store.add("First", first)
    projects = store.add("Second", second)
    projects = store.add("First", first)

    assert [project.name for project in projects] == ["First", "Second"]
    assert store.list() == projects


def test_recent_projects_drop_missing_paths(tmp_path):
    store = RecentProjectStore(tmp_path / "recent.json")
    missing = tmp_path / "missing.pfzip"
    store.path.write_text(
        '[{"name": "Missing", "path": "' + str(missing).replace('\\', '\\\\') + '"}]',
        encoding="utf-8",
    )

    assert store.list() == []