import os
from pathlib import Path

import pytest

from ac_tools.cli import Exit, main


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AC_STOPLIST", raising=False)
    monkeypatch.delenv("AC_CORPUS", raising=False)


def test_clean_repo_exits_ok_and_warns_about_skips(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main([str(repo)]) == Exit.OK

    err = capsys.readouterr().err
    assert "AC_STOPLIST not set: stoplist check skipped" in err
    assert "AC_CORPUS not set: overlap check skipped" in err


def test_findings_exit_one(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (repo / "plugins" / "core" / ".claude-plugin" / "plugin.json").unlink()

    assert main([str(repo)]) == Exit.FINDINGS
    assert "[manifest] plugins/core/.claude-plugin/plugin.json: missing file" in (
        capsys.readouterr().out
    )


def test_missing_plugins_dir_is_usage_error(tmp_path: Path) -> None:
    assert main([str(tmp_path)]) == Exit.USAGE


def test_stoplist_from_env(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    stoplist = tmp_path / "stop.txt"
    stoplist.write_text("alpha\n", encoding="utf-8")
    monkeypatch.setenv("AC_STOPLIST", str(stoplist))

    assert main([str(repo)]) == Exit.FINDINGS
    assert "[stoplist] plugins/core/skills/alpha/SKILL.md" in capsys.readouterr().out


def test_missing_stoplist_file_is_usage_error(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AC_STOPLIST", str(tmp_path / "absent.txt"))

    assert main([str(repo)]) == Exit.USAGE


def test_corpus_inside_repo_is_usage_error(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("AC_CORPUS", str(repo / "plugins"))

    assert main([str(repo)]) == Exit.USAGE
    assert "inside the checked repository" in capsys.readouterr().err


def test_corpus_overlap_from_env(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    phrase = "a b c d e f g h i j k l"
    (corpus / "x.md").write_text(phrase, encoding="utf-8")
    (repo / "plugins" / "core" / "skills" / "alpha" / "SKILL.md").write_text(
        f"---\nname: alpha\ndescription: Use when x\n---\n{phrase}\n", encoding="utf-8"
    )
    monkeypatch.setenv("AC_CORPUS", os.pathsep.join([str(corpus)]))

    assert main([str(repo)]) == Exit.FINDINGS
    assert "[overlap] plugins/core/skills/alpha/SKILL.md" in capsys.readouterr().out


def test_undecodable_stoplist_is_usage_error(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    stoplist = tmp_path / "stop.txt"
    stoplist.write_bytes(b"\xff\xfe")
    monkeypatch.setenv("AC_STOPLIST", str(stoplist))

    assert main([str(repo)]) == Exit.USAGE
    assert "cannot read" in capsys.readouterr().err
