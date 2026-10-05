from enum import StrEnum
from pathlib import Path

PLUGINS = "plugins"
SKILLS = "skills"


class Agent(StrEnum):
    CLAUDE = ".claude-plugin"
    CODEX = ".codex-plugin"
    CURSOR = ".cursor-plugin"


def plugin_dirs(repo: Path) -> list[Path]:
    root = repo / PLUGINS
    return sorted(path for path in root.iterdir() if path.is_dir()) if root.is_dir() else []
