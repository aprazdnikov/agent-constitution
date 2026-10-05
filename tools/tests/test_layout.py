from pathlib import Path

from ac_tools.findings import Check
from ac_tools.layout import load_texts, scanned_files


def test_scanned_files_scope(repo: Path) -> None:
    (repo / "docs" / "superpowers" / "specs").mkdir(parents=True)
    (repo / "docs" / "superpowers" / "specs" / "spec.md").write_text("x", encoding="utf-8")
    (repo / "docs" / "install.md").write_text("x", encoding="utf-8")
    (repo / "README.md").write_text("x", encoding="utf-8")
    (repo / "plugins" / "core" / "logo.png").write_bytes(b"\x89PNG")

    relative = [path.relative_to(repo).as_posix() for path in scanned_files(repo)]

    assert "docs/install.md" in relative
    assert "README.md" in relative
    assert "plugins/core/skills/alpha/SKILL.md" in relative
    assert "plugins/core/.claude-plugin/plugin.json" in relative
    assert "docs/superpowers/specs/spec.md" not in relative
    assert "plugins/core/logo.png" not in relative
    assert relative == sorted(relative)


def test_load_texts_normalizes_crlf_and_reports_bad_encoding(tmp_path: Path) -> None:
    good = tmp_path / "good.md"
    good.write_bytes(b"a\r\nb\r\n")
    bad = tmp_path / "bad.md"
    bad.write_bytes(b"\xff\xfe")

    texts, findings = load_texts([good, bad])

    assert texts == {good: "a\nb\n"}
    assert [(f.check, f.path) for f in findings] == [(Check.ENCODING, bad)]
