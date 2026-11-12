"""Hermes adapter for the shared core skills and constitution."""

from pathlib import Path
from typing import Protocol

ROOT = Path(__file__).resolve().parent
NAMES = {
    "modify-existing-code": "ac-core:modify-existing-code",
    "security-gate": "ac-core:security-gate",
    "postgres-migrations": "ac-postgres:postgres-migrations",
    "postgres-pgbouncer": "ac-postgres:postgres-pgbouncer",
}
MAX_HERMES_CONTEXT_CHARS = 4000


class Registry(Protocol):
    def register_skill(self, name: str, path: Path, description: str) -> object: ...

    def register_system_prompt_section(self, name: str, content: str) -> object: ...


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
    context = (ROOT / "hooks/constitution.md").read_text(encoding="utf-8").rstrip("\n")
    for name, qualified in NAMES.items():
        context = context.replace(f"`{name}`", f"`{qualified}`")
    if len(context) > MAX_HERMES_CONTEXT_CHARS:
        raise ValueError("constitution exceeds the Hermes system-section limit")
    ctx.register_system_prompt_section("agent-constitution.core", context)
