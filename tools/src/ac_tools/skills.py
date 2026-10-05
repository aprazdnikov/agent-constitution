import re
from collections.abc import Mapping
from pathlib import Path

import yaml

from ac_tools.findings import Check, Finding
from ac_tools.layout import SKILLS, plugin_dirs

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---(?:\n|\Z)", re.DOTALL)
PLACEHOLDER = re.compile(r"\b(TBD|TODO|FIXME)\b")
SKILL_FILE = "SKILL.md"


def skill_problems(directory: str, text: str) -> list[str]:
    match = FRONTMATTER.match(text)
    if match is None:
        return ["missing YAML frontmatter"]
    try:
        data: object = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return ["invalid YAML frontmatter"]
    if not isinstance(data, dict):
        return ["frontmatter must be a mapping"]
    name = data.get("name")
    description = data.get("description")
    problems = (
        [] if name == directory else [f"frontmatter name {name!r} != directory {directory!r}"]
    )
    if not isinstance(description, str) or not description.strip():
        problems.append("description must be a non-empty string")
    return problems


def _check_skill(directory: Path, texts: Mapping[Path, str]) -> list[Finding]:
    skill_md = directory / SKILL_FILE
    if not skill_md.is_file():
        return [Finding(Check.SKILL, directory, "missing SKILL.md")]
    text = texts.get(skill_md)
    if text is None:
        return []
    return [
        Finding(Check.SKILL, skill_md, problem) for problem in skill_problems(directory.name, text)
    ]


def check_skills(repo: Path, texts: Mapping[Path, str]) -> list[Finding]:
    directories = [
        directory
        for plugin in plugin_dirs(repo)
        if (plugin / SKILLS).is_dir()
        for directory in sorted((plugin / SKILLS).iterdir())
        if directory.is_dir()
    ]
    return [finding for directory in directories for finding in _check_skill(directory, texts)]


def check_placeholders(texts: Mapping[Path, str]) -> list[Finding]:
    return [
        Finding(Check.PLACEHOLDER, path, f"line {number}: placeholder {match.group(1)!r}")
        for path, text in texts.items()
        for number, line in enumerate(text.splitlines(), start=1)
        for match in PLACEHOLDER.finditer(line)
    ]
