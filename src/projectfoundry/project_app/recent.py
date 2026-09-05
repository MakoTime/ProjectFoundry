"""Application-local recent project references."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class RecentProject:
    """A user-facing reference to a project package."""

    name: str
    path: str
    format: str = "projectfoundry"
    last_opened: str = ""


class RecentProjectStore:
    """Persist recent project references in application data."""

    def __init__(self, path: str | Path, limit: int = 10) -> None:
        self.path = Path(path)
        self.limit = limit

    def list(self) -> list[RecentProject]:
        if not self.path.is_file():
            return []
        records = json.loads(self.path.read_text(encoding="utf-8"))
        return [RecentProject(**record) for record in records if Path(record["path"]).is_file()]

    def add(
        self,
        name: str,
        path: str | Path,
        format: str = "projectfoundry",
    ) -> list[RecentProject]:
        project_path = str(Path(path).resolve())
        projects = [project for project in self.list() if project.path != project_path]
        projects.insert(
            0,
            RecentProject(
                name=name,
                path=project_path,
                format=format,
                last_opened=datetime.now(timezone.utc).isoformat(),
            ),
        )
        projects = projects[: self.limit]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps([asdict(project) for project in projects], indent=2),
            encoding="utf-8",
        )
        return projects