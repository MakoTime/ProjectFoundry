"""Prepare a Project Foundry release."""

from __future__ import annotations

import argparse
import re
import subprocess
from datetime import date
from pathlib import Path

VERSION_PATTERN = re.compile(r'(__version__\s*=\s*["\'])(\d+\.\d+\.\d+)(["\'])')
TAG_PATTERN = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
VERSION_RELATIVE_PATH = Path("src/projectfoundry/__init__.py")
CHANGELOG_RELATIVE_PATH = Path("CHANGELOG.md")
VERSION_PATH = Path(__file__).resolve().parents[1] / "__init__.py"
CHANGELOG_PATH = Path(__file__).resolve().parents[2] / "CHANGELOG.md"


def read_version(path: Path = VERSION_PATH) -> str:
    match = VERSION_PATTERN.search(path.read_text(encoding="utf-8"))
    if match is None:
        raise ValueError(f"Could not find a semantic version in {path}")
    return match.group(2)


def increment_version(version: str, section: str) -> str:
    major, minor, patch = (int(part) for part in version.split("."))
    if section == "major":
        major, minor, patch = major + 1, 0, 0
    elif section == "minor":
        minor, patch = minor + 1, 0
    elif section == "patch":
        patch += 1
    else:
        raise ValueError(f"Unknown version section: {section}")
    return f"{major}.{minor}.{patch}"


def _git(*args: str, cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def repository_root() -> Path:
    return Path(_git("rev-parse", "--show-toplevel", cwd=Path.cwd()))


def latest_version_tag(root: Path) -> str | None:
    tags = _git("tag", "--list", "v*", cwd=root).splitlines()
    versions = [
        (tuple(int(part) for part in TAG_PATTERN.match(tag).groups()), tag)
        for tag in tags
        if TAG_PATTERN.match(tag)
    ]
    return max(versions)[1] if versions else None


def commit_subjects(root: Path, tag: str | None) -> list[str]:
    revision_range = f"{tag}..HEAD" if tag else "HEAD"
    output = _git("log", revision_range, "--format=%s", cwd=root)
    return [line for line in output.splitlines() if line]


def _changelog_section(subject: str) -> str:
    prefix = subject.split(":", 1)[0].lower()
    if prefix in {"add", "added", "feat", "feature"}:
        return "Added"
    if prefix in {"fix", "fixed", "bugfix"}:
        return "Fixed"
    return "Changed"


def changelog_entry(version: str, subjects: list[str], release_date: date | None = None) -> str:
    grouped: dict[str, list[str]] = {"Added": [], "Changed": [], "Fixed": []}
    for subject in subjects:
        grouped[_changelog_section(subject)].append(subject)
    lines = [f"## [{version}] - {(release_date or date.today()).isoformat()}", ""]
    for section, entries in grouped.items():
        if entries:
            lines.extend([f"### {section}", "", *[f"- {entry}" for entry in entries], ""])
    return "\n".join(lines).rstrip() + "\n"


def update_version(version: str, path: Path = VERSION_PATH) -> None:
    content = path.read_text(encoding="utf-8")
    updated, replacements = VERSION_PATTERN.subn(rf"\g<1>{version}\g<3>", content, count=1)
    if replacements != 1:
        raise ValueError(f"Could not update the semantic version in {path}")
    path.write_text(updated, encoding="utf-8")


def update_changelog(version: str, subjects: list[str], path: Path = CHANGELOG_PATH) -> None:
    content = path.read_text(encoding="utf-8") if path.exists() else (
        "# Changelog\n\nAll notable changes to Project Foundry are documented here.\n"
    )
    if re.search(rf"^## \[{re.escape(version)}\]", content, re.MULTILINE):
        raise ValueError(f"Changelog already contains version {version}")
    entry = changelog_entry(version, subjects)
    heading = re.search(r"^## \[", content, re.MULTILINE)
    if heading:
        updated = content[: heading.start()] + entry + "\n" + content[heading.start() :]
    else:
        updated = content.rstrip() + "\n\n" + entry
    path.write_text(updated, encoding="utf-8")


def prepare_release(section: str, root: Path | None = None) -> str:
    root = root or repository_root()
    if _git("status", "--porcelain", cwd=root):
        raise RuntimeError("Release preparation requires a clean working tree")
    version_path = root / VERSION_RELATIVE_PATH
    changelog_path = root / CHANGELOG_RELATIVE_PATH
    current = read_version(version_path)
    next_version = increment_version(current, section)
    tag = latest_version_tag(root)
    update_version(next_version, version_path)
    update_changelog(next_version, commit_subjects(root, tag), changelog_path)
    return next_version


def finish_release(version: str, root: Path, *, commit: bool, tag: bool, push: bool) -> None:
    if push and not (commit and tag):
        raise ValueError("--push requires --commit and --tag")
    if not (commit or tag or push):
        return
    if commit:
        _git("add", str(VERSION_RELATIVE_PATH), str(CHANGELOG_RELATIVE_PATH), cwd=root)
        _git("commit", "-m", f"Release v{version}", cwd=root)
    if tag:
        _git("tag", f"v{version}", cwd=root)
    if push:
        _git("push", "--follow-tags", cwd=root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--version-part", choices=("patch", "minor", "major"),
        help="Version section to increment",
    )
    parser.add_argument("--commit", action="store_true", help="Create the release commit")
    parser.add_argument("--tag", action="store_true", help="Create the release tag")
    parser.add_argument("--push", action="store_true", help="Push the release commit and tag")
    parser.add_argument("--dry-run", action="store_true", help="Show the next version only")
    args = parser.parse_args(argv)
    root = repository_root()
    current = read_version(root / VERSION_RELATIVE_PATH)
    section = args.version_part
    if section is None:
        print("Select version increment: 1) patch  2) minor  3) major")
        choice = input("Choice: ").strip()
        section = {"1": "patch", "2": "minor", "3": "major"}.get(choice)
        if section is None:
            print("No release prepared.")
            return 1
    next_version = increment_version(current, section)
    if args.dry_run:
        print(f"Next version: {next_version}")
        return 0
    prepared_version = prepare_release(section, root)
    finish_release(
        prepared_version,
        root,
        commit=args.commit,
        tag=args.tag,
        push=args.push,
    )
    print(f"Prepared release {prepared_version}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
