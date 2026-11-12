from pathlib import Path

import pytest

from ac_tools.qwen_sandbox import BundleError, create_bundle

ROOT = Path(__file__).resolve().parents[2]


def test_bundle_routes_to_local_skill_files_and_keeps_references(tmp_path: Path) -> None:
    project = tmp_path / "project-plugin"
    skill = project / "skills/project-context"
    (skill / "references").mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: project-context\ndescription: Use for the demo project.\n---\n"
        "Read references/project.md.\n",
        encoding="utf-8",
    )
    (skill / "references/project.md").write_text("Approved project context\n", encoding="utf-8")
    recipe = project / "skills/new-service"
    recipe.mkdir()
    (recipe / "SKILL.md").write_text(
        "---\nname: new-service\ndescription: Use when adding a service --- or job.\n"
        "---  \nCreate it.\n",
        encoding="utf-8",
    )
    output = tmp_path / "bundle"

    create_bundle(output, ROOT / "plugins/core", [ROOT / "plugins/postgres", project])

    context = (output / "QWEN.md").read_text(encoding="utf-8")
    assert "read_file" in context
    assert "absolute path" in context
    assert ".agent-constitution/skills/security-gate/SKILL.md" in context
    assert ".agent-constitution/skills/project-context/SKILL.md" in context
    assert "Confirm security-sensitive actions" in context
    assert "PostgreSQL skill files are included in this local bundle" in context
    assert "give each subagent the paths" in context
    assert "Use when adding a service --- or job." in context
    assert (output / ".agent-constitution/skills/project-context/references/project.md").read_text(
        encoding="utf-8"
    ) == "Approved project context\n"
    assert (
        output / ".agent-constitution/skills/postgres-migrations/references/lock-levels.md"
    ).is_file()


def test_existing_output_is_preserved(tmp_path: Path) -> None:
    output = tmp_path / "bundle"
    output.mkdir()
    marker = output / "QWEN.md"
    marker.write_text("Existing rules\n", encoding="utf-8")

    with pytest.raises(BundleError, match="already exists"):
        create_bundle(output, ROOT / "plugins/core", [])

    assert marker.read_text(encoding="utf-8") == "Existing rules\n"


def test_bundle_rejects_symlinks_without_creating_output(tmp_path: Path) -> None:
    plugin = tmp_path / "other-plugin"
    skill = plugin / "skills/extra"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("extra\n", encoding="utf-8")
    (skill / "outside").symlink_to(tmp_path)
    output = tmp_path / "bundle"

    with pytest.raises(BundleError, match="symlink"):
        create_bundle(output, ROOT / "plugins/core", [plugin])

    assert not output.exists()


def test_bundle_rejects_a_linked_skills_directory(tmp_path: Path) -> None:
    plugin = tmp_path / "other-plugin"
    plugin.mkdir()
    (plugin / "skills").symlink_to(ROOT / "plugins/postgres/skills", target_is_directory=True)

    with pytest.raises(BundleError, match="symlink"):
        create_bundle(tmp_path / "bundle", ROOT / "plugins/core", [plugin])

    assert not (tmp_path / "bundle").exists()


def test_bundle_rejects_skill_name_collisions(tmp_path: Path) -> None:
    plugin = tmp_path / "other-plugin"
    skill = plugin / "skills/security-gate"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("different skill\n", encoding="utf-8")

    with pytest.raises(BundleError, match="duplicate skill"):
        create_bundle(tmp_path / "bundle", ROOT / "plugins/core", [plugin])

    assert not (tmp_path / "bundle").exists()


def test_bundle_rejects_recipe_without_a_description_before_writing(tmp_path: Path) -> None:
    plugin = tmp_path / "other-plugin"
    skill = plugin / "skills/new-service"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: new-service\n---\nDo work.\n", encoding="utf-8")

    with pytest.raises(BundleError, match="description"):
        create_bundle(tmp_path / "bundle", ROOT / "plugins/core", [plugin])

    assert not (tmp_path / "bundle").exists()
