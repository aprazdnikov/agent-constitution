import importlib.util
import json
import shutil
import subprocess
from pathlib import Path
from types import ModuleType

import pytest
import yaml

from ac_tools.qwen_hooks import render

ROOT = Path(__file__).resolve().parents[2]


class HermesRegistry:
    def __init__(self) -> None:
        self.skills: dict[str, tuple[Path, str]] = {}
        self.sections: dict[str, str] = {}

    def register_skill(self, name: str, path: Path, description: str) -> None:
        self.skills[name] = (path, description)

    def register_system_prompt_section(self, name: str, content: str) -> None:
        self.sections[name] = content


def _load(plugin: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"ac_test_{plugin.name}", plugin / "__init__.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("plugin", "skills"),
    [
        ("core", {"modify-existing-code", "security-gate"}),
        ("postgres", {"postgres-migrations", "postgres-pgbouncer"}),
    ],
)
def test_hermes_registers_packaged_skills_with_descriptions(plugin: str, skills: set[str]) -> None:
    path = ROOT / "plugins" / plugin
    registry = HermesRegistry()
    _load(path).register(registry)

    assert registry.skills.keys() == skills
    for name, (skill_file, description) in registry.skills.items():
        assert skill_file == path / "skills" / name / "SKILL.md"
        assert skill_file.is_file()
        assert description


def test_hermes_core_routes_to_namespaced_skills_and_includes_constitution() -> None:
    registry = HermesRegistry()
    _load(ROOT / "plugins/core").register(registry)

    assert len(registry.sections) == 1
    context = next(iter(registry.sections.values()))
    assert "Confirm security-sensitive actions" in context
    assert "`ac-core:security-gate`" in context
    assert "`ac-postgres:postgres-migrations`" in context
    assert len(context) <= 4000


@pytest.mark.parametrize("event", ["SessionStart", "SubagentStart"])
def test_qwen_hook_prints_current_constitution_and_namespaced_routes(event: str) -> None:
    root = ROOT / "plugins/core"
    manifest = json.loads((root / "qwen-extension.json").read_text(encoding="utf-8"))
    hooks = json.loads((root / manifest["hooks"]).read_text(encoding="utf-8"))["hooks"]
    command = hooks[event][0]["hooks"][0]["command"]
    shell = shutil.which("sh")
    assert shell is not None
    result = subprocess.run(
        [shell, "-c", command], capture_output=True, text=True, check=True, timeout=10
    )

    output = json.loads(result.stdout)["hookSpecificOutput"]
    assert output["hookEventName"] == event
    context = output["additionalContext"]
    original = (root / "hooks/constitution.md").read_text(encoding="utf-8").rstrip("\n")
    for skill, qualified in (
        ("modify-existing-code", "core:modify-existing-code"),
        ("security-gate", "core:security-gate"),
        ("postgres-migrations", "postgres:postgres-migrations"),
        ("postgres-pgbouncer", "postgres:postgres-pgbouncer"),
    ):
        original = original.replace(f"`{skill}`", f"`{qualified}`")
    assert context == original


def test_qwen_hook_treats_shell_syntax_as_context_data(tmp_path: Path) -> None:
    marker = tmp_path / "unexpected"
    context = f"A quote ' and a substitution $(touch {marker}) are project text."
    command = json.loads(render(context))["hooks"]["SessionStart"][0]["hooks"][0]["command"]
    shell = shutil.which("sh")
    assert shell is not None
    result = subprocess.run(
        [shell, "-c", command], capture_output=True, text=True, check=True, timeout=10
    )

    assert json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"] == context
    assert not marker.exists()


def test_qwen_hook_rejects_the_extension_loader_placeholder() -> None:
    with pytest.raises(ValueError, match="CLAUDE_PLUGIN_ROOT"):
        render("Literal ${CLAUDE_PLUGIN_ROOT} inside the context")


@pytest.mark.parametrize("plugin", ["core", "postgres"])
def test_qwen_extension_keeps_plugin_version_and_packaged_skills(plugin: str) -> None:
    root = ROOT / "plugins" / plugin
    native = json.loads((root / "qwen-extension.json").read_text(encoding="utf-8"))
    claude = json.loads((root / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
    assert native["name"] == plugin
    assert native["version"] == claude["version"]
    assert (root / native["skills"]).is_dir()


@pytest.mark.parametrize("plugin", ["core", "postgres"])
def test_hermes_manifest_matches_shared_plugin_version(plugin: str) -> None:
    root = ROOT / "plugins" / plugin
    manifest = yaml.safe_load((root / "plugin.yaml").read_text(encoding="utf-8"))
    claude = json.loads((root / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
    assert manifest["name"] == f"ac-{plugin}"
    assert manifest["version"] == claude["version"]
