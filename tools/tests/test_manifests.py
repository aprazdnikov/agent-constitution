from pathlib import Path

from ac_tools.findings import Check
from ac_tools.manifests import check_manifests
from tests.builders import drop_key, patch_json


def _messages(repo: Path) -> list[str]:
    return [finding.message for finding in check_manifests(repo)]


def _manifest(repo: Path, agent: str) -> Path:
    return repo / "plugins" / "core" / agent / "plugin.json"


def test_valid_repo_has_no_findings(repo: Path) -> None:
    assert check_manifests(repo) == []


def test_missing_manifest_is_reported(repo: Path) -> None:
    path = _manifest(repo, ".cursor-plugin")
    path.unlink()

    [finding] = check_manifests(repo)

    assert finding.check is Check.MANIFEST
    assert finding.path == path
    assert finding.message == "missing file"


def test_invalid_json_is_reported(repo: Path) -> None:
    _manifest(repo, ".codex-plugin").write_text("{", encoding="utf-8")

    [finding] = check_manifests(repo)

    assert finding.message.startswith("invalid JSON")


def test_version_drift_is_reported(repo: Path) -> None:
    patch_json(_manifest(repo, ".codex-plugin"), "version", "0.2.0")

    assert _messages(repo) == [
        "versions differ across agents: "
        ".claude-plugin=0.1.0, .codex-plugin=0.2.0, .cursor-plugin=0.1.0",
    ]


def test_name_must_match_directory(repo: Path) -> None:
    patch_json(_manifest(repo, ".claude-plugin"), "name", "other")

    assert _messages(repo) == [".claude-plugin: name 'other' != directory 'core'"]


def test_version_must_be_semver(repo: Path) -> None:
    for agent in (".claude-plugin", ".codex-plugin", ".cursor-plugin"):
        patch_json(_manifest(repo, agent), "version", "1.0")

    assert _messages(repo) == [
        ".claude-plugin: version '1.0' is not MAJOR.MINOR.PATCH",
        ".codex-plugin: version '1.0' is not MAJOR.MINOR.PATCH",
        ".cursor-plugin: version '1.0' is not MAJOR.MINOR.PATCH",
    ]


def test_description_drift_is_reported(repo: Path) -> None:
    patch_json(_manifest(repo, ".cursor-plugin"), "description", "different")

    assert _messages(repo) == ["descriptions differ across agents"]


def test_skills_path_required_when_plugin_has_skills(repo: Path) -> None:
    drop_key(_manifest(repo, ".cursor-plugin"), "skills")

    assert _messages(repo) == [".cursor-plugin: skills must be './skills/'"]


def test_missing_string_field_is_reported(repo: Path) -> None:
    drop_key(_manifest(repo, ".claude-plugin"), "version")

    assert _messages(repo) == ["field 'version' must be a string"]
