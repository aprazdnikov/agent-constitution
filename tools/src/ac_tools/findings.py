from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class Check(StrEnum):
    MANIFEST = "manifest"
    MARKETPLACE = "marketplace"
    SKILL = "skill"
    PLACEHOLDER = "placeholder"
    STOPLIST = "stoplist"
    OVERLAP = "overlap"
    ENCODING = "encoding"
    HOOKS = "hooks"


@dataclass(frozen=True, slots=True)
class Finding:
    check: Check
    path: Path
    message: str

    def render(self, root: Path) -> str:
        return f"[{self.check}] {self.path.relative_to(root).as_posix()}: {self.message}"
