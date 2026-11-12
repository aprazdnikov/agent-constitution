"""Build Qwen hook output from the shared constitution without interpolating paths in a shell."""

import argparse
import json
import shlex
from pathlib import Path

NAMES = {
    "modify-existing-code": "core:modify-existing-code",
    "security-gate": "core:security-gate",
    "postgres-migrations": "postgres:postgres-migrations",
    "postgres-pgbouncer": "postgres:postgres-pgbouncer",
}


def render(context: str) -> str:
    if "${CLAUDE_PLUGIN_ROOT}" in context:
        raise ValueError("context must not contain the Qwen loader token ${CLAUDE_PLUGIN_ROOT}")
    context = context.rstrip("\n")
    for name, qualified in NAMES.items():
        context = context.replace(f"`{name}`", f"`{qualified}`")
    hooks: dict[str, list[dict[str, object]]] = {}
    for event in ("SessionStart", "SubagentStart"):
        output = {"hookSpecificOutput": {"hookEventName": event, "additionalContext": context}}
        command = "printf '%s\\n' " + shlex.quote(json.dumps(output, ensure_ascii=False))
        hooks[event] = [{"hooks": [{"type": "command", "command": command, "timeout": 30}]}]
    return json.dumps({"hooks": hooks}, indent=2, ensure_ascii=False) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="core plugin directory")
    root = parser.parse_args().root
    content = (root / "hooks/constitution.md").read_text(encoding="utf-8")
    (root / "hooks/qwen-hooks.json").write_text(render(content), encoding="utf-8")


if __name__ == "__main__":
    main()
