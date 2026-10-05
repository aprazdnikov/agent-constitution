import json
from collections.abc import Mapping, Sequence
from pathlib import Path

VERSION = "0.1.0"


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _load(path: Path) -> dict[str, object]:
    data: dict[str, object] = json.loads(path.read_text(encoding="utf-8"))
    return data


def patch_json(path: Path, key: str, value: object) -> None:
    write_json(path, {**_load(path), key: value})


def drop_key(path: Path, key: str) -> None:
    write_json(path, {k: v for k, v in _load(path).items() if k != key})


def _write_plugin(repo: Path, name: str, skills: Sequence[str]) -> None:
    plugin = repo / "plugins" / name
    description = f"{name} plugin"
    write_json(
        plugin / ".claude-plugin" / "plugin.json",
        {"name": name, "version": VERSION, "description": description},
    )
    for agent in (".codex-plugin", ".cursor-plugin"):
        write_json(
            plugin / agent / "plugin.json",
            {"name": name, "version": VERSION, "description": description, "skills": "./skills/"},
        )
    for skill in skills:
        skill_md = plugin / "skills" / skill / "SKILL.md"
        skill_md.parent.mkdir(parents=True)
        skill_md.write_text(
            f"---\nname: {skill}\ndescription: Use when testing {skill}\n---\n\n# {skill}\n",
            encoding="utf-8",
        )


def _write_marketplaces(repo: Path, names: Sequence[str]) -> None:
    owner = {"name": "Test"}
    write_json(
        repo / ".claude-plugin" / "marketplace.json",
        {
            "name": "test",
            "owner": owner,
            "plugins": [{"name": n, "source": f"./plugins/{n}"} for n in names],
        },
    )
    write_json(
        repo / ".cursor-plugin" / "marketplace.json",
        {
            "name": "test",
            "owner": owner,
            "metadata": {"pluginRoot": "plugins"},
            "plugins": [{"name": n, "source": n} for n in names],
        },
    )
    write_json(
        repo / ".agents" / "plugins" / "marketplace.json",
        {
            "name": "test",
            "interface": {"displayName": "Test"},
            "plugins": [
                {
                    "name": n,
                    "source": {"source": "local", "path": f"./plugins/{n}"},
                    "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                    "category": "Productivity",
                }
                for n in names
            ],
        },
    )


def write_repo(root: Path, plugins: Mapping[str, Sequence[str]]) -> Path:
    for name, skills in plugins.items():
        _write_plugin(root, name, skills)
    _write_marketplaces(root, sorted(plugins))
    return root
