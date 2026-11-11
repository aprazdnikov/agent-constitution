#!/usr/bin/env python3
"""Add the core constitution to a Cursor Task without an explicit permission decision."""

import json
import sys
from pathlib import Path


def main() -> int:
    try:
        data = json.load(sys.stdin)
        if not isinstance(data, dict) or data.get("tool_name") != "Task":
            raise ValueError("expected Task hook input")
        task = data.get("tool_input")
        if not isinstance(task, dict) or not isinstance(task.get("prompt"), str):
            raise ValueError("expected a Task prompt")
        constitution = Path(__file__).with_name("constitution.md").read_text(encoding="utf-8")
        if not constitution.strip():
            raise ValueError("empty constitution")
    except (OSError, ValueError):
        print("cursor-subagent: invalid input or unavailable constitution", file=sys.stderr)
        return 1
    json.dump(
        {"updated_input": {"prompt": constitution.rstrip("\n") + "\n\n" + task["prompt"]}},
        sys.stdout,
        ensure_ascii=False,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
