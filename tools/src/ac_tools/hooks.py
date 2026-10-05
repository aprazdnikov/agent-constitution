from collections.abc import Callable
from pathlib import Path

from ac_tools.findings import Check, Finding
from ac_tools.jsonio import ManifestError, load_object, object_field, object_list, text_field
from ac_tools.layout import Agent, plugin_dirs

HOOKS_DIR = "hooks"
SHARED_HOOKS = "hooks.json"
CURSOR_HOOKS_VERSION = 1


def _check_shared(obj: dict[str, object]) -> None:
    events = object_field(obj, "hooks")
    for event in sorted(events):
        for group in object_list(events, event):
            for handler in object_list(group, "hooks"):
                if text_field(handler, "type") != "command":
                    msg = f"{event}: handler type must be 'command'"
                    raise ManifestError(msg)
                text_field(handler, "command")


def _check_cursor(obj: dict[str, object]) -> None:
    version = obj.get("version")
    if type(version) is not int or version != CURSOR_HOOKS_VERSION:
        msg = f"field 'version' must be {CURSOR_HOOKS_VERSION}"
        raise ManifestError(msg)
    events = object_field(obj, "hooks")
    for event in sorted(events):
        for handler in object_list(events, event):
            text_field(handler, "command")


def _cursor_hooks_path(plugin: Path) -> Path:
    relative = load_object(plugin / Agent.CURSOR / "plugin.json").get("hooks")
    if not isinstance(relative, str):
        msg = "cursor manifest must set 'hooks' to a Cursor-format file"
        raise ManifestError(msg)
    path = (plugin / relative).resolve()
    if not path.is_relative_to(plugin.resolve()):
        msg = "cursor hooks file must stay inside the plugin"
        raise ManifestError(msg)
    return path


def _file_findings(path: Path, check: Callable[[dict[str, object]], None]) -> list[Finding]:
    try:
        check(load_object(path))
    except ManifestError as error:
        return [Finding(Check.HOOKS, path, str(error))]
    return []


def _check_plugin(plugin: Path) -> list[Finding]:
    findings = _file_findings(plugin / HOOKS_DIR / SHARED_HOOKS, _check_shared)
    try:
        cursor = _cursor_hooks_path(plugin)
    except ManifestError as error:
        manifest = plugin / Agent.CURSOR / "plugin.json"
        return [*findings, Finding(Check.HOOKS, manifest, str(error))]
    return findings + _file_findings(cursor, _check_cursor)


def check_hooks(repo: Path) -> list[Finding]:
    return [
        finding
        for plugin in plugin_dirs(repo)
        if (plugin / HOOKS_DIR).is_dir()
        for finding in _check_plugin(plugin)
    ]
