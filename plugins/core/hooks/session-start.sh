#!/bin/sh
# Prints constitution.md as session or subagent context.
# No argument: Claude Code and Codex session. "subagent": their subagent. "cursor": Cursor session.
set -eu

case "${1:-}" in
  "" | cursor | subagent) ;;
  *) echo "session-start: unknown format '$1'" >&2; exit 2 ;;
esac

here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
payload="$here/constitution.md"
if [ ! -f "$payload" ]; then
  echo "session-start: missing $payload" >&2
  exit 1
fi

text=$(sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' "$payload" | awk 'NR > 1 { printf "\\n" } { printf "%s", $0 }')

case "${1:-}" in
  cursor) printf '{"additional_context":"%s"}\n' "$text" ;;
  subagent) printf '{"hookSpecificOutput":{"hookEventName":"SubagentStart","additionalContext":"%s"}}\n' "$text" ;;
  *) printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$text" ;;
esac
