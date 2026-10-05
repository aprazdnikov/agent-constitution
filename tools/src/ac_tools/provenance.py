import re
from collections.abc import Mapping, Sequence
from pathlib import Path

from ac_tools.findings import Check, Finding

WINDOW = 12
WORD = re.compile(r"\w+")
MARKDOWN = ".md"


def load_stoplist(path: Path) -> frozenset[str]:
    lines = (line.strip().lower() for line in path.read_text(encoding="utf-8").splitlines())
    return frozenset(line for line in lines if line and not line.startswith("#"))


def _term_pattern(term: str) -> re.Pattern[str]:
    return re.compile(rf"(?<!\w){re.escape(term)}(?!\w)")


def check_stoplist(texts: Mapping[Path, str], stoplist: frozenset[str]) -> list[Finding]:
    patterns = [(term, _term_pattern(term)) for term in sorted(stoplist)]
    lowered = {path: text.lower() for path, text in texts.items()}
    return [
        Finding(Check.STOPLIST, path, f"contains stoplisted term {term!r}")
        for path, text in lowered.items()
        for term, pattern in patterns
        if pattern.search(text)
    ]


def _shingles(text: str, window: int) -> set[tuple[str, ...]]:
    words = WORD.findall(text.lower())
    return {tuple(words[i : i + window]) for i in range(len(words) - window + 1)}


def corpus_shingles(directories: Sequence[Path], window: int) -> set[tuple[str, ...]]:
    return {
        shingle
        for directory in directories
        for path in sorted(directory.rglob(f"*{MARKDOWN}"))
        # Third-party text: one bad byte must not disable the whole check.
        for shingle in _shingles(path.read_text(encoding="utf-8", errors="replace"), window)
    }


def _overlap(path: Path, text: str, corpus: set[tuple[str, ...]], window: int) -> list[Finding]:
    hits = _shingles(text, window) & corpus
    if not hits:
        return []
    example = " ".join(min(hits))
    message = f"{len(hits)} shared {window}-word phrase(s), e.g. {example!r}"
    return [Finding(Check.OVERLAP, path, message)]


def check_overlap(
    texts: Mapping[Path, str], corpus: set[tuple[str, ...]], window: int
) -> list[Finding]:
    return [
        finding
        for path, text in texts.items()
        if path.suffix == MARKDOWN
        for finding in _overlap(path, text, corpus, window)
    ]
