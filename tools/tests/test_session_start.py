import json
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "plugins" / "core" / "hooks" / "session-start.sh"
PAYLOAD = 'Rules:\n- a "quoted" word and a back\\slash survive\n- ✅ unicode survives\n'
EXPECTED = PAYLOAD.rstrip("\n")


@pytest.fixture
def hooks_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "hooks"
    directory.mkdir()
    shutil.copy(SCRIPT, directory / "session-start.sh")
    (directory / "constitution.md").write_text(PAYLOAD, encoding="utf-8")
    return directory


def _run(hooks_dir: Path, *args: str) -> subprocess.CompletedProcess[str]:
    sh = shutil.which("sh")
    assert sh is not None
    return subprocess.run(
        [sh, str(hooks_dir / "session-start.sh"), *args],
        capture_output=True,
        encoding="utf-8",
        check=False,
        timeout=10,
        cwd=hooks_dir.parent,
    )


def test_default_output_is_claude_and_codex_context(hooks_dir: Path) -> None:
    result = _run(hooks_dir)

    assert result.returncode == 0
    assert json.loads(result.stdout) == {
        "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": EXPECTED}
    }


def test_cursor_output(hooks_dir: Path) -> None:
    result = _run(hooks_dir, "cursor")

    assert result.returncode == 0
    assert json.loads(result.stdout) == {"additional_context": EXPECTED}


def test_subagent_output_is_context_for_claude_and_codex(hooks_dir: Path) -> None:
    result = _run(hooks_dir, "subagent")

    assert result.returncode == 0
    assert json.loads(result.stdout) == {
        "hookSpecificOutput": {"hookEventName": "SubagentStart", "additionalContext": EXPECTED}
    }


def test_core_registers_subagent_context_hooks() -> None:
    hooks = SCRIPT.parent
    shared = json.loads((hooks / "hooks.json").read_text(encoding="utf-8"))["hooks"]
    cursor = json.loads((hooks / "cursor-hooks.json").read_text(encoding="utf-8"))["hooks"]

    assert any(
        "subagent" in handler["command"]
        for group in shared["SubagentStart"]
        for handler in group["hooks"]
    )
    assert "preToolUse" not in cursor


def test_unknown_format_is_rejected(hooks_dir: Path) -> None:
    result = _run(hooks_dir, "vim")

    assert result.returncode == 2
    assert "unknown format 'vim'" in result.stderr
    assert result.stdout == ""


def test_missing_payload_fails(hooks_dir: Path) -> None:
    (hooks_dir / "constitution.md").unlink()

    result = _run(hooks_dir)

    assert result.returncode == 1
    assert "constitution.md" in result.stderr
    assert result.stdout == ""
