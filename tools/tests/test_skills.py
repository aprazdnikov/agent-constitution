from pathlib import Path

from ac_tools.findings import Check, Finding
from ac_tools.layout import load_texts, scanned_files
from ac_tools.skills import check_placeholders, check_skills


def _skill_md(repo: Path) -> Path:
    return repo / "plugins" / "core" / "skills" / "alpha" / "SKILL.md"


def _skill_messages(repo: Path) -> list[str]:
    texts, _ = load_texts(scanned_files(repo))
    return [finding.message for finding in check_skills(repo, texts)]


def test_valid_skills_have_no_findings(repo: Path) -> None:
    assert _skill_messages(repo) == []


def test_missing_skill_md_is_reported(repo: Path) -> None:
    _skill_md(repo).unlink()
    texts, _ = load_texts(scanned_files(repo))

    [finding] = check_skills(repo, texts)

    assert finding.check is Check.SKILL
    assert finding.path == _skill_md(repo).parent
    assert finding.message == "missing SKILL.md"


def test_name_must_match_directory(repo: Path) -> None:
    _skill_md(repo).write_text("---\nname: other\ndescription: Use when x\n---\n", encoding="utf-8")

    assert _skill_messages(repo) == ["frontmatter name 'other' != directory 'alpha'"]


def test_missing_frontmatter_is_reported(repo: Path) -> None:
    _skill_md(repo).write_text("# alpha\n", encoding="utf-8")

    assert _skill_messages(repo) == ["missing YAML frontmatter"]


def test_empty_description_is_reported(repo: Path) -> None:
    _skill_md(repo).write_text("---\nname: alpha\ndescription: '  '\n---\n", encoding="utf-8")

    assert _skill_messages(repo) == ["description must be a non-empty string"]


def test_non_mapping_frontmatter_is_reported(repo: Path) -> None:
    _skill_md(repo).write_text("---\n- a\n- b\n---\n", encoding="utf-8")

    assert _skill_messages(repo) == ["frontmatter must be a mapping"]


def test_crlf_frontmatter_is_accepted(repo: Path) -> None:
    path = _skill_md(repo)
    path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))

    assert _skill_messages(repo) == []


def test_placeholders_are_reported_with_line(tmp_path: Path) -> None:
    path = tmp_path / "a.md"
    texts = {path: "fine\nfill TBD later\nTODOS and todo are fine\n"}

    assert check_placeholders(texts) == [
        Finding(Check.PLACEHOLDER, path, "line 2: placeholder 'TBD'"),
    ]
