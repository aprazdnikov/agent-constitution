import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "plugins/core/hooks/cursor-subagent.py"
PAYLOAD = 'Follow "rules" and path C:\\repo.\n规则.\n'


@pytest.fixture
def hooks_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "hooks"
    directory.mkdir()
    if SCRIPT.is_file():
        shutil.copy(SCRIPT, directory / SCRIPT.name)
    (directory / "constitution.md").write_text(PAYLOAD, encoding="utf-8")
    return directory


def _run(hooks_dir: Path, text: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(hooks_dir / SCRIPT.name)],
        input=text,
        capture_output=True,
        encoding="utf-8",
        check=False,
        timeout=10,
    )


def test_cursor_task_gets_rules_without_explicit_permission_decision(hooks_dir: Path) -> None:
    prompt = 'Investigate "a"\n研发'
    task = {"prompt": prompt, "description": "short", "readonly": True}
    result = _run(hooks_dir, json.dumps({"tool_name": "Task", "tool_input": task}))

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output == {"updated_input": {"prompt": PAYLOAD.rstrip() + "\n\n" + prompt}}
    assert "permission" not in output


@pytest.mark.parametrize("bad_input", ["not json", "{}", '{"tool_input": {"prompt": 123}}'])
def test_invalid_task_fails_without_printing_input(hooks_dir: Path, bad_input: str) -> None:
    result = _run(hooks_dir, bad_input)

    assert result.returncode != 0
    assert result.stdout == ""
    assert bad_input not in result.stderr
