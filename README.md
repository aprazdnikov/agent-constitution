# Agent Constitution

Production rules and skills for coding agents — Claude Code, Codex and Cursor — packaged as plugins.
Install them once and every session starts with the same engineering discipline instead of each developer prompting the agent their own way.

## Plugins

| Plugin | What it adds |
|---|---|
| `core` | A short constitution injected at session start, plus the skills `modify-existing-code` (careful changes to code the agent did not write) and `security-gate` (a security pass on every programming task) |
| `postgres` | The skills `postgres-migrations` (lock-aware schema changes) and `postgres-pgbouncer` (what breaks behind transaction pooling) |

Install `core` first; `postgres` is optional. See [docs/install.md](docs/install.md).

## Repository layout

```
.claude-plugin/marketplace.json     Claude Code marketplace
.cursor-plugin/marketplace.json     Cursor marketplace
.agents/plugins/marketplace.json    Codex marketplace
plugins/<name>/                     one plugin: three agent manifests, skills/, hooks/
docs/evals/                         evaluation scenarios for every skill
tools/                              ac-check, the repository validator
```

## Validation

`ac-check` keeps the three agent formats in sync: manifest versions and descriptions, marketplace entries, hook configs, skill frontmatter, and leftover placeholders.

```bash
cd tools && uv sync && uv run ac-check ..
```

## Paid plugins

Language rules (Python, Rust, Go, TypeScript, Java) and `codify` — a skill that derives house rules from a team's own repository with verified evidence — are coming soon.
