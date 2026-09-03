"""Install or update Project Foundry instructions in another project."""

from __future__ import annotations

import argparse
from importlib.resources import files
from pathlib import Path

START_MARKER = "<!-- Project Foundry managed instructions -->\n<projectfoundry>"
END_MARKER = "</projectfoundry>\n<!-- End Project Foundry managed instructions -->"


def instruction_block() -> str:
    content = files("projectfoundry.templates").joinpath("copilot-instructions.md").read_text(
        encoding="utf-8"
    )
    return f"{START_MARKER}\n{content.rstrip()}\n{END_MARKER}"


def update_instructions(project_root: str | Path, *, remove: bool = False) -> tuple[Path, bool]:
    root = Path(project_root).resolve()
    github_dir = root / ".github"
    instruction_path = github_dir / "copilot-instructions.md"
    original = instruction_path.read_text(encoding="utf-8") if instruction_path.exists() else ""
    start = original.find("<!-- Project Foundry managed instructions -->")
    end = original.find(END_MARKER)
    if original.count("<!-- Project Foundry managed instructions -->") > 1:
        raise ValueError("Project Foundry instruction markers appear multiple times")
    if original.count(END_MARKER) > 1:
        raise ValueError("Project Foundry instruction markers appear multiple times")
    if (start == -1) != (end == -1):
        raise ValueError("Project Foundry instruction markers are incomplete")
    if start != -1:
        end += len(END_MARKER)
        if remove:
            prefix = original[:start].rstrip()
            suffix = original[end:].lstrip()
            if prefix and suffix:
                updated = prefix + "\n\n" + suffix
            else:
                updated = prefix or suffix
        else:
            updated = original[:start] + instruction_block() + original[end:]
    elif remove:
        return instruction_path, False
    else:
        updated = original.rstrip()
        if updated:
            updated += "\n\n"
        updated += instruction_block() + "\n"
    if updated == original:
        return instruction_path, False
    github_dir.mkdir(parents=True, exist_ok=True)
    instruction_path.write_text(updated, encoding="utf-8")
    return instruction_path, True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--check", action="store_true", help="Report whether the managed block exists"
    )
    parser.add_argument(
        "--remove", action="store_true", help="Remove the managed instruction block"
    )
    args = parser.parse_args(argv)
    path = args.project_root.resolve() / ".github" / "copilot-instructions.md"
    if args.check:
        content = path.read_text(encoding="utf-8") if path.exists() else ""
        if ("<!-- Project Foundry managed instructions -->" in content) != (END_MARKER in content):
            raise ValueError("Project Foundry instruction markers are incomplete")
        print("installed" if START_MARKER in content and END_MARKER in content else "not installed")
        return 0
    update_instructions(args.project_root, remove=args.remove)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
