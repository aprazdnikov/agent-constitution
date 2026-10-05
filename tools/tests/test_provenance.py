from pathlib import Path

from ac_tools.findings import Check, Finding
from ac_tools.provenance import (
    WINDOW,
    check_overlap,
    check_stoplist,
    corpus_shingles,
    load_stoplist,
)

NUMBERS = "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen"


def test_load_stoplist_skips_comments_and_blanks(tmp_path: Path) -> None:
    path = tmp_path / "stop.txt"
    path.write_text("# comment\n\nAcme\n  Foo Bar  \n", encoding="utf-8")

    assert load_stoplist(path) == frozenset({"acme", "foo bar"})


def test_stoplist_matches_case_insensitively(tmp_path: Path) -> None:
    path = tmp_path / "a.md"

    findings = check_stoplist({path: "Built at ACME bank"}, frozenset({"acme"}))

    assert findings == [Finding(Check.STOPLIST, path, "contains stoplisted term 'acme'")]


def test_stoplist_respects_word_boundaries(tmp_path: Path) -> None:
    assert check_stoplist({tmp_path / "a.md": "acmeology"}, frozenset({"acme"})) == []


def _corpus(tmp_path: Path) -> set[tuple[str, ...]]:
    corpus_dir = tmp_path / "corpus"
    (corpus_dir / "nested").mkdir(parents=True)
    (corpus_dir / "nested" / "a.md").write_text(NUMBERS, encoding="utf-8")
    return corpus_shingles([corpus_dir], WINDOW)


def test_overlap_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "rule.md"
    shared = " ".join(NUMBERS.split()[1:13])

    [finding] = check_overlap({path: f"Intro. {shared}. Outro."}, _corpus(tmp_path), WINDOW)

    assert finding.check is Check.OVERLAP
    assert finding.message == f"1 shared {WINDOW}-word phrase(s), e.g. '{shared}'"


def test_overlap_ignores_case_and_punctuation(tmp_path: Path) -> None:
    path = tmp_path / "rule.md"
    shouted = ", ".join(word.upper() for word in NUMBERS.split()[:12])

    assert len(check_overlap({path: shouted}, _corpus(tmp_path), WINDOW)) == 1


def test_short_shared_phrase_is_not_reported(tmp_path: Path) -> None:
    path = tmp_path / "rule.md"
    eleven = " ".join(NUMBERS.split()[:11])

    assert check_overlap({path: eleven}, _corpus(tmp_path), WINDOW) == []


def test_overlap_scans_markdown_only(tmp_path: Path) -> None:
    path = tmp_path / "plugin.json"

    assert check_overlap({path: NUMBERS}, _corpus(tmp_path), WINDOW) == []
