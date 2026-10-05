from collections.abc import Mapping
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import assert_never

from ac_tools.findings import Check, Finding
from ac_tools.jsonio import ManifestError, load_object, object_field, object_list, text_field
from ac_tools.layout import PLUGINS, plugin_dirs


class Marketplace(StrEnum):
    CLAUDE = ".claude-plugin/marketplace.json"
    CURSOR = ".cursor-plugin/marketplace.json"
    CODEX = ".agents/plugins/marketplace.json"


def _source(kind: Marketplace, entry: dict[str, object], plugin_root: str) -> str:
    match kind:
        case Marketplace.CLAUDE:
            return PurePosixPath(text_field(entry, "source")).as_posix()
        case Marketplace.CODEX:
            return PurePosixPath(text_field(object_field(entry, "source"), "path")).as_posix()
        case Marketplace.CURSOR:
            return (PurePosixPath(plugin_root) / text_field(entry, "source")).as_posix()
        case _:
            assert_never(kind)


def sources(kind: Marketplace, obj: dict[str, object]) -> dict[str, str]:
    plugin_root = (
        text_field(object_field(obj, "metadata"), "pluginRoot")
        if kind is Marketplace.CURSOR
        else ""
    )
    return {
        text_field(entry, "name"): _source(kind, entry, plugin_root)
        for entry in object_list(obj, "plugins")
    }


def marketplace_problems(actual: Mapping[str, str], expected: Mapping[str, str]) -> list[str]:
    missing = [f"{name}: missing" for name in sorted(expected.keys() - actual.keys())]
    unknown = [
        f"{name}: no such plugin directory" for name in sorted(actual.keys() - expected.keys())
    ]
    wrong = [
        f"{name}: source resolves to {actual[name]!r}, expected {expected[name]!r}"
        for name in sorted(actual.keys() & expected.keys())
        if actual[name] != expected[name]
    ]
    return missing + unknown + wrong


def _check(repo: Path, kind: Marketplace, expected: Mapping[str, str]) -> list[Finding]:
    path = repo / kind
    try:
        actual = sources(kind, load_object(path))
    except ManifestError as error:
        return [Finding(Check.MARKETPLACE, path, str(error))]
    return [
        Finding(Check.MARKETPLACE, path, problem)
        for problem in marketplace_problems(actual, expected)
    ]


def check_marketplaces(repo: Path) -> list[Finding]:
    expected = {plugin.name: f"{PLUGINS}/{plugin.name}" for plugin in plugin_dirs(repo)}
    return [finding for kind in Marketplace for finding in _check(repo, kind, expected)]
