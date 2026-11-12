"""Prepare a reviewable local skills bundle for Qwen's tool-execution sandbox."""

import argparse
import re
import shutil
import sys
from collections.abc import Sequence
from pathlib import Path

import yaml

SKILL_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
ROUTED = (
    "modify-existing-code",
    "security-gate",
    "postgres-migrations",
    "postgres-pgbouncer",
)


class BundleError(Exception):
    """The requested bundle cannot be safely assembled."""


def _description(skill: Path) -> str:
    lines = (skill / "SKILL.md").read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise BundleError(f"invalid skill frontmatter: {skill.name}")
    end = next((index for index, line in enumerate(lines[1:], 1) if line.strip() == "---"), None)
    if end is None:
        raise BundleError(f"invalid skill frontmatter: {skill.name}")
    try:
        metadata = yaml.safe_load("\n".join(lines[1:end]))
    except yaml.YAMLError as error:
        raise BundleError(f"invalid skill frontmatter: {skill.name}") from error
    description = metadata.get("description") if isinstance(metadata, dict) else None
    if not isinstance(description, str) or not description.strip():
        raise BundleError(f"missing skill description: {skill.name}")
    return " ".join(description.split())


def _skills(plugins: Sequence[Path]) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for plugin in plugins:
        skills = plugin / "skills"
        if plugin.is_symlink() or skills.is_symlink():
            raise BundleError(f"symlink in skill source: {plugin}")
        if not skills.is_dir():
            raise BundleError(f"missing skills directory: {skills}")
        for skill in sorted(skills.iterdir()):
            if skill.is_symlink():
                raise BundleError(f"symlink in skill source: {skill}")
            if not skill.is_dir() or not (skill / "SKILL.md").is_file():
                continue
            if not SKILL_NAME.fullmatch(skill.name):
                raise BundleError(f"invalid skill name: {skill.name}")
            if skill.name in found:
                raise BundleError(f"duplicate skill: {skill.name}")
            for path in skill.rglob("*"):
                if path.is_symlink():
                    raise BundleError(f"symlink in skill source: {path}")
                if not (path.is_file() or path.is_dir()):
                    raise BundleError(f"unsupported file type: {path}")
            found[skill.name] = skill
    return found


def _context(core: Path, skills: dict[str, Path]) -> str:
    source = core / "hooks/constitution.md"
    if source.is_symlink() or source.parent.is_symlink():
        raise BundleError("constitution must not be a symlink")
    text = source.read_text(encoding="utf-8").rstrip("\n")
    postgres = {"postgres-migrations", "postgres-pgbouncer"}
    if postgres.intersection(skills) and not postgres.issubset(skills):
        raise BundleError("include both PostgreSQL skills or neither")
    postgres_note = (
        "PostgreSQL skill files are included in this local bundle."
        if postgres.issubset(skills)
        else "PostgreSQL skill files are not included; skip their rows and report that limitation."
    )
    replacements = {
        (
            "Before acting, check whether your situation matches a row below. "
            "If it does, invoke the named skill first and follow it."
        ): (
            "Before acting, check the rows below. If one applies, use read_file to read the "
            "named local SKILL.md and follow it. Resolve each path from the workspace root "
            "and pass its absolute path to read_file."
        ),
        (
            "The `postgres-migrations` and `postgres-pgbouncer` skills exist only when the "
            "`postgres` plugin is installed; if it is not, skip those rows and note that "
            "they were unavailable."
        ): postgres_note,
        (
            "Whenever a situation in the routing list applies, invoking its skill is required, "
            "not optional."
        ): ("When a routing row applies, read and follow its local skill file."),
        "tell each subagent to use the skills relevant to its work": (
            "give each subagent the paths to its relevant local skill files "
            "and tell it to read them"
        ),
    }
    for old, new in replacements.items():
        if text.count(old) != 1:
            raise BundleError("constitution routing changed; update the sandbox adapter")
        text = text.replace(old, new)
    for name in ROUTED:
        if name in skills:
            text = text.replace(f"`{name}`", f"`.agent-constitution/skills/{name}/SKILL.md`")
    if "codify-repo" in skills:
        text += (
            "\n\nWhen the team explicitly requests project-knowledge initialization or an update, "
            "read `.agent-constitution/skills/codify-repo/SKILL.md` and follow it."
        )
    if "project-context" in skills:
        text += (
            "\n\nFor work on this business project, read "
            "`.agent-constitution/skills/project-context/SKILL.md` and its relevant references."
        )
    recipes = sorted(set(skills) - set(ROUTED) - {"codify-repo", "project-context"})
    if recipes:
        text += "\n\nOther locally available skills; read the relevant file for the task:\n"
        text += "\n".join(
            f"- `.agent-constitution/skills/{name}/SKILL.md`: {_description(skills[name])}"
            for name in recipes
        )
    return text + "\n"


def create_bundle(destination: Path, core: Path, additional_plugins: Sequence[Path]) -> None:
    """Build a new bundle; never merge or overwrite a project's existing files."""
    if destination.exists() or destination.is_symlink():
        raise BundleError(f"output already exists: {destination}")
    plugins = [core, *additional_plugins]
    if any(destination.resolve().is_relative_to(plugin.resolve()) for plugin in plugins):
        raise BundleError("output must be outside the source plugins")
    skills = _skills(plugins)
    if not {"modify-existing-code", "security-gate"}.issubset(skills):
        raise BundleError("the bundle requires both core skills")
    context = _context(core, skills)
    destination.mkdir()
    local_skills = destination / ".agent-constitution/skills"
    local_skills.mkdir(parents=True)
    for name, source in skills.items():
        shutil.copytree(
            source,
            local_skills / name,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
    (destination / "QWEN.md").write_text(context, encoding="utf-8")
    (destination / "README.md").write_text(
        "Review this bundle. Merge QWEN.md with any existing project instructions; "
        "do not overwrite them. Copy .agent-constitution into the intended project only "
        "after checking for existing files. Keep project knowledge within its approved scope.\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="new bundle directory")
    parser.add_argument("--core", type=Path, required=True, help="core plugin directory")
    parser.add_argument(
        "--plugin", type=Path, action="append", default=[], help="additional plugin"
    )
    args = parser.parse_args()
    try:
        create_bundle(args.output, args.core, args.plugin)
    except (BundleError, OSError) as error:
        sys.stderr.write(f"qwen-sandbox: {error}\n")
        raise SystemExit(2) from error
    sys.stdout.write(f"Bundle prepared for review: {args.output}\n")


if __name__ == "__main__":
    main()
