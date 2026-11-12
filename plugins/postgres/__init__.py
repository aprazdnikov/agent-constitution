"""Hermes adapter for the shared PostgreSQL skills."""

from pathlib import Path
from typing import Protocol

ROOT = Path(__file__).resolve().parent


class Registry(Protocol):
    def register_skill(self, name: str, path: Path, description: str) -> object: ...


def _description(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines()[1:]:
        if line == "---":
            break
        if line.startswith("description: "):
            return line.removeprefix("description: ").strip()
    raise ValueError(f"missing single-line skill description: {path}")


def register(ctx: Registry) -> None:
    for skill in sorted((ROOT / "skills").iterdir()):
        path = skill / "SKILL.md"
        if path.is_file():
            ctx.register_skill(skill.name, path, _description(path))
