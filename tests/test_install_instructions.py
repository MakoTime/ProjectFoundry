import pytest

from projectfoundry.scripts.install_instructions import (
    END_MARKER,
    START_MARKER,
    main,
    update_instructions,
)


def test_update_creates_managed_block_and_preserves_user_text(tmp_path):
    path = tmp_path / ".github" / "copilot-instructions.md"
    path.parent.mkdir()
    path.write_text("# Consumer rules\n\n- Keep API stable.\n", encoding="utf-8")

    updated_path, changed = update_instructions(tmp_path)
    content = updated_path.read_text(encoding="utf-8")

    assert changed
    assert "# Consumer rules" in content
    assert "- Keep API stable." in content
    assert content.count(START_MARKER) == 1
    assert content.count(END_MARKER) == 1


def test_update_is_idempotent_and_refreshes_only_managed_block(tmp_path):
    update_instructions(tmp_path)
    path = tmp_path / ".github" / "copilot-instructions.md"
    first = path.read_text(encoding="utf-8")
    _, changed = update_instructions(tmp_path)

    assert not changed
    assert path.read_text(encoding="utf-8") == first


def test_remove_deletes_only_managed_block(tmp_path):
    path = tmp_path / ".github" / "copilot-instructions.md"
    path.parent.mkdir()
    path.write_text(
        "User text\n\n" + START_MARKER + "\nmanaged\n" + END_MARKER + "\nTail\n",
        encoding="utf-8",
    )

    _, changed = update_instructions(tmp_path, remove=True)
    content = path.read_text(encoding="utf-8")

    assert changed
    assert content == "User text\n\nTail\n"


def test_check_does_not_modify_files(tmp_path, capsys):
    assert main(["--project-root", str(tmp_path), "--check"]) == 0
    assert capsys.readouterr().out.strip() == "not installed"
    assert not (tmp_path / ".github").exists()


def test_incomplete_markers_are_rejected(tmp_path):
    path = tmp_path / ".github" / "copilot-instructions.md"
    path.parent.mkdir()
    path.write_text(START_MARKER + "\nmanaged\n", encoding="utf-8")

    with pytest.raises(ValueError, match="incomplete"):
        update_instructions(tmp_path)


def test_duplicate_managed_blocks_are_rejected(tmp_path):
    path = tmp_path / ".github" / "copilot-instructions.md"
    path.parent.mkdir()
    block = START_MARKER + "\nmanaged\n" + END_MARKER
    path.write_text(block + "\n\n" + block, encoding="utf-8")

    with pytest.raises(ValueError, match="multiple"):
        update_instructions(tmp_path)
