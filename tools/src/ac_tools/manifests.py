import re
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from ac_tools.findings import Check, Finding
from ac_tools.jsonio import ManifestError, load_object, text_field
from ac_tools.layout import SKILLS, Agent, plugin_dirs

SEMVER = re.compile(r"\d+\.\d+\.\d+")
SKILLS_PATH = "./skills/"


class Skills(Enum):
    PRESENT = "present"
    ABSENT = "absent"


@dataclass(frozen=True, slots=True)
class Manifest:
    agent: Agent
    name: str
    version: str
    description: str
    skills: str | None


def _read(path: Path, agent: Agent) -> Manifest:
    obj = load_object(path)
    skills = obj.get("skills")
    return Manifest(
        agent=agent,
        name=text_field(obj, "name"),
        version=text_field(obj, "version"),
        description=text_field(obj, "description"),
        skills=skills if isinstance(skills, str) else None,
    )


def manifest_problems(plugin: str, manifests: Sequence[Manifest], skills: Skills) -> list[str]:
    problems = [
        f"{m.agent}: name {m.name!r} != directory {plugin!r}" for m in manifests if m.name != plugin
    ]
    problems += [
        f"{m.agent}: version {m.version!r} is not MAJOR.MINOR.PATCH"
        for m in manifests
        if not SEMVER.fullmatch(m.version)
    ]
    if len({m.version for m in manifests}) > 1:
        versions = ", ".join(f"{m.agent}={m.version}" for m in manifests)
        problems.append(f"versions differ across agents: {versions}")
    if len({m.description for m in manifests}) > 1:
        problems.append("descriptions differ across agents")
    if skills is Skills.PRESENT:
        problems += [
            f"{m.agent}: skills must be {SKILLS_PATH!r}"
            for m in manifests
            if m.agent is not Agent.CLAUDE and m.skills != SKILLS_PATH
        ]
    return problems


def _check_plugin(plugin: Path) -> list[Finding]:
    findings: list[Finding] = []
    manifests: list[Manifest] = []
    for agent in Agent:
        path = plugin / agent / "plugin.json"
        try:
            manifests.append(_read(path, agent))
        except ManifestError as error:
            findings.append(Finding(Check.MANIFEST, path, str(error)))
    skills = Skills.PRESENT if (plugin / SKILLS).is_dir() else Skills.ABSENT
    problems = manifest_problems(plugin.name, manifests, skills)
    return findings + [Finding(Check.MANIFEST, plugin, problem) for problem in problems]


def check_manifests(repo: Path) -> list[Finding]:
    return [finding for plugin in plugin_dirs(repo) for finding in _check_plugin(plugin)]
