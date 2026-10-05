from pathlib import Path

from ac_tools.findings import Check
from ac_tools.hooks import check_hooks
from tests.builders import drop_key, patch_json, write_json

SHARED: dict[str, object] = {
    "hooks": {
        "SessionStart": [
            {"matcher": "startup", "hooks": [{"type": "command", "command": "sh x.sh"}]}
        ]
    }
}
CURSOR: dict[str, object] = {
    "version": 1,
    "hooks": {"sessionStart": [{"command": "sh ./hooks/x.sh cursor"}]},
}


def _with_hooks(repo: Path) -> Path:
    plugin = repo / "plugins" / "core"
    write_json(plugin / "hooks" / "hooks.json", SHARED)
    write_json(plugin / "hooks" / "cursor-hooks.json", CURSOR)
    patch_json(plugin / ".cursor-plugin" / "plugin.json", "hooks", "./hooks/cursor-hooks.json")
    return plugin


def _messages(repo: Path) -> list[str]:
    return [finding.message for finding in check_hooks(repo)]


def test_plugin_without_hooks_has_no_findings(repo: Path) -> None:
    assert check_hooks(repo) == []


def test_valid_hooks_have_no_findings(repo: Path) -> None:
    _with_hooks(repo)

    assert check_hooks(repo) == []


def test_cursor_manifest_must_point_at_cursor_hooks(repo: Path) -> None:
    plugin = _with_hooks(repo)
    drop_key(plugin / ".cursor-plugin" / "plugin.json", "hooks")

    [finding] = check_hooks(repo)

    assert finding.check is Check.HOOKS
    assert finding.path == plugin / ".cursor-plugin" / "plugin.json"
    assert finding.message == "cursor manifest must set 'hooks' to a Cursor-format file"


def test_cursor_hooks_must_stay_inside_plugin(repo: Path) -> None:
    plugin = _with_hooks(repo)
    patch_json(plugin / ".cursor-plugin" / "plugin.json", "hooks", "../postgres/x.json")

    assert _messages(repo) == ["cursor hooks file must stay inside the plugin"]


def test_shared_hooks_require_wrapper(repo: Path) -> None:
    plugin = _with_hooks(repo)
    write_json(plugin / "hooks" / "hooks.json", SHARED["hooks"])

    assert _messages(repo) == ["field 'hooks' must be an object"]


def test_shared_handler_must_be_command(repo: Path) -> None:
    plugin = _with_hooks(repo)
    handler = {"type": "prompt", "command": "x"}
    write_json(plugin / "hooks" / "hooks.json", {"hooks": {"SessionStart": [{"hooks": [handler]}]}})

    assert _messages(repo) == ["SessionStart: handler type must be 'command'"]


def test_cursor_version_must_be_integer_one(repo: Path) -> None:
    plugin = _with_hooks(repo)
    patch_json(plugin / "hooks" / "cursor-hooks.json", "version", True)

    assert _messages(repo) == ["field 'version' must be 1"]


def test_cursor_handler_needs_command(repo: Path) -> None:
    plugin = _with_hooks(repo)
    patch_json(plugin / "hooks" / "cursor-hooks.json", "hooks", {"sessionStart": [{"timeout": 30}]})

    assert _messages(repo) == ["field 'command' must be a string"]
