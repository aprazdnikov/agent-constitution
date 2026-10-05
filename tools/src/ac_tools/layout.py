from collections.abc import Iterable
from enum import StrEnum
from pathlib import Path, PurePosixPath

from ac_tools.findings import Check, Finding

PLUGINS = "plugins"
SKILLS = "skills"
DOCS = "docs"
EXCLUDED_DOCS = PurePosixPath("docs/superpowers")
README = "README.md"
TEXT_SUFFIXES = frozenset({".md", ".json", ".py", ".sh", ".cmd", ".txt", ".yaml", ".yml", ".toml"})


class Agent(StrEnum):
    CLAUDE = ".claude-plugin"
    CODEX = ".codex-plugin"
    CURSOR = ".cursor-plugin"


def plugin_dirs(repo: Path) -> list[Path]:
    root = repo / PLUGINS
    return sorted(path for path in root.iterdir() if path.is_dir()) if root.is_dir() else []


def _in_scope(repo: Path, path: Path) -> bool:
    relative = PurePosixPath(path.relative_to(repo).as_posix())
    return (
        path.is_file()
        and path.suffix in TEXT_SUFFIXES
        and not relative.is_relative_to(EXCLUDED_DOCS)
    )


def scanned_files(repo: Path) -> list[Path]:
    roots = [repo / PLUGINS, repo / DOCS]
    files = [
        path for root in roots if root.is_dir() for path in root.rglob("*") if _in_scope(repo, path)
    ]
    readme = repo / README
    return sorted([*files, readme] if readme.is_file() else files)


def load_texts(files: Iterable[Path]) -> tuple[dict[Path, str], list[Finding]]:
    texts: dict[Path, str] = {}
    findings: list[Finding] = []
    for path in files:
        try:
            texts[path] = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        except UnicodeDecodeError:
            findings.append(Finding(Check.ENCODING, path, "not valid UTF-8"))
    return texts, findings
