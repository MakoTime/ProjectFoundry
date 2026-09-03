from datetime import date

import projectfoundry.scripts.release as release
from projectfoundry.scripts.release import (
    changelog_entry,
    increment_version,
    update_changelog,
    update_version,
)


def test_increment_version_sections():
    assert increment_version("1.2.3", "patch") == "1.2.4"
    assert increment_version("1.2.3", "minor") == "1.3.0"
    assert increment_version("1.2.3", "major") == "2.0.0"


def test_changelog_entry_groups_commit_subjects():
    entry = changelog_entry(
        "1.3.0",
        ["feat: add release command", "fix: handle missing tags", "refactor: simplify parser"],
        date(2026, 9, 4),
    )

    assert entry == (
        "## [1.3.0] - 2026-09-04\n\n"
        "### Added\n\n- feat: add release command\n\n"
        "### Changed\n\n- refactor: simplify parser\n\n"
        "### Fixed\n\n- fix: handle missing tags\n"
    )


def test_update_version_and_changelog(tmp_path):
    version_path = tmp_path / "__init__.py"
    changelog_path = tmp_path / "CHANGELOG.md"
    version_path.write_text('__version__ = "0.1.0"\n', encoding="utf-8")
    changelog_path.write_text("# Changelog\n", encoding="utf-8")

    update_version("0.2.0", version_path)
    update_changelog("0.2.0", ["feat: add release command"], changelog_path)

    assert ' __version__ = "0.2.0"' not in version_path.read_text(encoding="utf-8")
    assert '__version__ = "0.2.0"' in version_path.read_text(encoding="utf-8")
    assert "## [0.2.0]" in changelog_path.read_text(encoding="utf-8")


def test_pre_push_allows_a_version_with_a_matching_tag(tmp_path, monkeypatch, capsys):
    version_path = tmp_path / "src" / "projectfoundry" / "__init__.py"
    version_path.parent.mkdir(parents=True)
    version_path.write_text('__version__ = "0.1.0"\n', encoding="utf-8")
    monkeypatch.setattr(release, "VERSION_RELATIVE_PATH", version_path.relative_to(tmp_path))
    monkeypatch.setattr(release, "repository_root", lambda: tmp_path)
    monkeypatch.setattr(release, "latest_version_tag", lambda root: "v0.1.0")

    assert release.main(["--pre-push"]) == 0
    assert "already prepared" in capsys.readouterr().out