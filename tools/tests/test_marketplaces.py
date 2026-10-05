import json
from pathlib import Path

from ac_tools.findings import Check
from ac_tools.marketplaces import check_marketplaces
from tests.builders import patch_json


def _load(path: Path) -> dict[str, object]:
    data: dict[str, object] = json.loads(path.read_text(encoding="utf-8"))
    return data


def test_valid_repo_has_no_findings(repo: Path) -> None:
    assert check_marketplaces(repo) == []


def test_plugin_missing_from_marketplace(repo: Path) -> None:
    path = repo / ".claude-plugin" / "marketplace.json"
    patch_json(path, "plugins", [{"name": "core", "source": "./plugins/core"}])

    [finding] = check_marketplaces(repo)

    assert finding.check is Check.MARKETPLACE
    assert finding.path == path
    assert finding.message == "postgres: missing"


def test_unknown_plugin_is_reported(repo: Path) -> None:
    path = repo / ".agents" / "plugins" / "marketplace.json"
    entries = _load(path)["plugins"]
    assert isinstance(entries, list)
    ghost = {"name": "ghost", "source": {"source": "local", "path": "./plugins/ghost"}}
    patch_json(path, "plugins", [*entries, ghost])

    assert [f.message for f in check_marketplaces(repo)] == ["ghost: no such plugin directory"]


def test_wrong_source_is_reported(repo: Path) -> None:
    path = repo / ".cursor-plugin" / "marketplace.json"
    patch_json(
        path,
        "plugins",
        [{"name": "core", "source": "elsewhere"}, {"name": "postgres", "source": "postgres"}],
    )

    assert [f.message for f in check_marketplaces(repo)] == [
        "core: source resolves to 'plugins/elsewhere', expected 'plugins/core'",
    ]


def test_missing_marketplace_file_is_reported(repo: Path) -> None:
    (repo / ".claude-plugin" / "marketplace.json").unlink()

    assert [f.message for f in check_marketplaces(repo)] == ["missing file"]


def test_cursor_requires_plugin_root(repo: Path) -> None:
    patch_json(repo / ".cursor-plugin" / "marketplace.json", "metadata", {})

    assert [f.message for f in check_marketplaces(repo)] == ["field 'pluginRoot' must be a string"]
