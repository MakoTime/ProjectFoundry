import re

from projectfoundry import __version__, update_instructions


def test_package_version() -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+", __version__)


def test_update_instructions_is_available_from_package_root(tmp_path) -> None:
    path, changed = update_instructions(tmp_path)

    assert changed
    assert path == tmp_path / ".github" / "copilot-instructions.md"
