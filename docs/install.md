# Installing Agent Constitution

This repository is a plugin marketplace named `agent-constitution`. It ships two plugins:

| Plugin | What it adds |
| :- | :- |
| `core` | Hooks for session and subagent context, plus the skills `modify-existing-code` and `security-gate`. |
| `postgres` | The skills `postgres-migrations` and `postgres-pgbouncer`. Optional. |

Install `core` first. The constitution it injects is what routes the agent to every skill, including the
`postgres` ones, so `postgres` on its own gives you skills that nothing tells the agent to use.

Every command below links to the page or source file it was taken from. The repository is published at
`https://github.com/aprazdnikov/agent-constitution`. Where an agent can also read a marketplace from disk,
the local form assumes a clone:

```bash
git clone https://github.com/aprazdnikov/agent-constitution.git
```

- [Claude Code](#claude-code)
- [Codex](#codex)
- [Qwen Code](#qwen-code)
- [Hermes](#hermes)
- [OpenCode](#opencode)
- [Cursor](#cursor)
- [Limitations](#limitations)

## Claude Code

Claude Code reads `.claude-plugin/marketplace.json` at the repository root.

### Add the marketplace

From GitHub
([source](https://code.claude.com/docs/en/plugins/install#add-a-marketplace)):

```bash
claude plugin marketplace add aprazdnikov/agent-constitution
```

From a local clone. Start a relative path with `./` or `../`, otherwise Claude Code reads it as a GitHub
`owner/repo`
([source](https://code.claude.com/docs/en/plugins/install#add-a-marketplace)):

```bash
claude plugin marketplace add ./agent-constitution
```

Inside a running session, the same sources work with `/plugin marketplace add`
([source](https://code.claude.com/docs/en/plugins/install#add-a-marketplace)).

### Install the plugins

Install `core`
([source](https://code.claude.com/docs/en/plugins/install#install-from-your-shell)):

```bash
claude plugin install core@agent-constitution
```

Optionally install `postgres`
([source](https://code.claude.com/docs/en/plugins/install#install-from-your-shell)):

```bash
claude plugin install postgres@agent-constitution
```

Both install at user scope by default; pass `--scope project` or `--scope local` to change that
([source](https://code.claude.com/docs/en/plugins/install#install-from-your-shell)). Inside a session,
`/plugin install core@agent-constitution` opens the plugin's details so you can pick a scope there
([source](https://code.claude.com/docs/en/plugins/install#install-a-plugin)).

Plugins installed from the shell load in the next session, or after `/reload-plugins` in an open one
([source](https://code.claude.com/docs/en/plugins/install#install-from-your-shell)). To check the install,
run `claude plugin list`
([source](https://code.claude.com/docs/en/plugins/install#install-a-plugin)).

### Confirm the hook ran

1. Start a new session with `claude`.
2. Ask: "Which rules and skills are active in this session?"
3. The answer should describe the Agent Constitution: its engineering principles and its skill-routing
   list, which sends edits to existing code to `modify-existing-code`, any programming task to
   `security-gate`, PostgreSQL migration files and live-database DDL to `postgres-migrations`, and
   relevant connection-pooling work to `postgres-pgbouncer`. Without `postgres`, the agent should
   say those two rows are unavailable.

If the agent does not mention the constitution or its routing, the hook did not run. Typing `/` should
still list the skills as `/core:modify-existing-code` and `/core:security-gate`, which tells you the
plugin itself loaded.

## Codex

Codex reads `.agents/plugins/marketplace.json` at the repository root. The commands below come from the
Codex CLI source, because the Codex documentation site (`developers.openai.com/codex`) returned HTTP 403
when this guide was written. All source links point to
[openai/codex](https://github.com/openai/codex) at commit `7f892275e31002f0422477c6219189284560e689`.

### Add the marketplace

From GitHub
([source](https://github.com/openai/codex/blob/7f892275e31002f0422477c6219189284560e689/codex-rs/cli/src/marketplace_cmd.rs#L60-L64)):

```bash
codex plugin marketplace add aprazdnikov/agent-constitution
```

From a local clone
([source](https://github.com/openai/codex/blob/7f892275e31002f0422477c6219189284560e689/codex-rs/cli/src/marketplace_cmd.rs#L60-L64)):

```bash
codex plugin marketplace add ./agent-constitution
```

`codex plugin marketplace list` shows the marketplaces Codex knows about
([source](https://github.com/openai/codex/blob/7f892275e31002f0422477c6219189284560e689/codex-rs/cli/src/marketplace_cmd.rs#L88)).

### Install the plugins

Install `core`
([source](https://github.com/openai/codex/blob/7f892275e31002f0422477c6219189284560e689/codex-rs/cli/src/plugin_cmd.rs#L80-L84)):

```bash
codex plugin add core@agent-constitution
```

Optionally install `postgres`
([source](https://github.com/openai/codex/blob/7f892275e31002f0422477c6219189284560e689/codex-rs/cli/src/plugin_cmd.rs#L80-L84)):

```bash
codex plugin add postgres@agent-constitution
```

`codex plugin list` shows what is installed
([source](https://github.com/openai/codex/blob/7f892275e31002f0422477c6219189284560e689/codex-rs/cli/src/plugin_cmd.rs#L99-L103)).
Inside the TUI, `/plugins` browses plugins
([source](https://github.com/openai/codex/blob/7f892275e31002f0422477c6219189284560e689/codex-rs/tui/src/slash_command.rs#L154)).

### Approve the hook

Codex does not run a plugin hook until you trust it. When you start the TUI with an untrusted hook, it
offers "Review hooks", "Trust all and continue", and "Continue without trusting (hooks won't run)"
([source](https://github.com/openai/codex/blob/7f892275e31002f0422477c6219189284560e689/codex-rs/tui/src/startup_hooks_review.rs#L263-L274)).
Pick one of the first two and approve the `core` session-start hook. `/hooks` in the TUI lets you view
and manage hooks later
([source](https://github.com/openai/codex/blob/7f892275e31002f0422477c6219189284560e689/codex-rs/tui/src/slash_command.rs#L116)).

Codex records trust as a hash of the hook entry: its event, matcher, command and timeout. When a plugin
update changes that entry, the hook's status becomes "modified" and it stops running until you approve it
again
([source](https://github.com/openai/codex/blob/7f892275e31002f0422477c6219189284560e689/codex-rs/hooks/src/engine/discovery.rs#L777-L813)).
Approve the hook in the TUI before relying on non-interactive runs such as `codex exec`, which have no
approval prompt.

### Confirm the hook ran

1. Start a new session with `codex`, approving the hook if asked.
2. Ask: "Which rules and skills are active in this session?"
3. The answer should describe the Agent Constitution and its skill-routing list, naming
   `modify-existing-code`, `security-gate`, and, when `postgres` is installed, `postgres-migrations` and
   `postgres-pgbouncer`.

If the answer says nothing about the constitution, open `/hooks` and check whether the `core` hook is
untrusted or modified.

## Qwen Code

Clone the Git repository, then install the native extensions from the business project's working directory:

```bash
qwen extensions install /path/to/agent-constitution/plugins/core --scope project
qwen extensions install /path/to/agent-constitution/plugins/postgres --scope project
qwen extensions list
```

The PostgreSQL extension is optional. Review the extension consent prompt. The `core` extension includes `SessionStart` and `SubagentStart` context hooks and routes to the Qwen namespaced skills; restarting the session activates changes. The installed Qwen version and its settings determine whether extensions and hooks run. With Qwen Code 0.27.0, local extension installation, skill discovery, session and subagent context, and skill loading were checked using a local model stub. In a non-interactive session the `skill` and `agent` tools can require explicit permission; narrowly allowed tools were used for those synthetic checks. Qwen's optional [execution sandbox](https://qwenlm.github.io/qwen-code-docs/en/users/features/sandbox/) disables executable extensions, hooks and the skill tool; use the local-file bundle below in that mode.

### Qwen tool-execution sandbox

The sandbox bundle is a reviewable set of local instruction files, not an executable extension. It lets the agent read the applicable `SKILL.md` and references with `read_file` without changing sandbox settings. Generate it in a **new** directory outside the source plugins:

```bash
cd /path/to/agent-constitution/tools
uv run python -m ac_tools.qwen_sandbox \
  --output /path/to/new-review-bundle \
  --core ../plugins/core \
  --plugin ../plugins/postgres
```

Omit the PostgreSQL `--plugin` argument and the preceding continuation character when it is not needed. To include Pro or approved project knowledge, repeat `--plugin` with `/path/to/agent-constitution-pro/plugins/codify` or `/path/to/knowledge-target/plugins/project`. Include project knowledge only for its own business project and keep the review bundle in an appropriately protected location. The tool rejects duplicate skill names, source symlinks and an existing output directory.

Review the generated `QWEN.md` and `.agent-constitution/skills/`. In each intended project, merge the generated `QWEN.md` with any existing project instructions and copy the `.agent-constitution` directory only after checking for existing files and approving conflicts. Do not overwrite unrelated rules. Restart Qwen and verify that it reads the local paths. Synthetic Qwen 0.27.0 sessions in a Landlock sandbox loaded the generated context in the main session and a subagent, and read the security skill, `codify`, and a project reference using a local model stub. Model adherence and a full project initialization remain to be tested. The sandbox still limits writes to its admitted workspace, so choose a knowledge target compatible with that boundary. Do not disable the sandbox automatically.

The bundle is a copy and does not update itself. After an approved plugin or knowledge update, generate a new bundle, review its differences and update the project's copies deliberately.

When editing `plugins/core/hooks/constitution.md`, regenerate the Qwen hook payload and run the tests:

```bash
cd /path/to/agent-constitution/tools
uv run python -m ac_tools.qwen_hooks ../plugins/core
uv run pytest tests/test_agent_integrations.py
```

## Hermes

Hermes uses its own plugin format and requires explicit enablement. Install from the Git repository and review the plugin before enabling it:

```bash
hermes plugins install aprazdnikov/agent-constitution/plugins/core --no-enable
hermes plugins enable ac-core
hermes plugins install aprazdnikov/agent-constitution/plugins/postgres --no-enable
hermes plugins enable ac-postgres
```

The PostgreSQL plugin is optional. `ac-core` registers the constitution as a system-prompt section and exposes `ac-core:modify-existing-code` and `ac-core:security-gate`; the PostgreSQL skills use the `ac-postgres:` namespace. Plugin registration and main/subagent context delivery were checked with Hermes 0.22.5 and a local model stub. The synthetic check used `hermes -z`, which bypasses approval prompts, only with a temporary configuration and test data. Hermes may omit plugins in safe mode or when they are not enabled; behavior with real models still needs evaluation.

For a local clone, copy each plugin directory to the corresponding `~/.hermes/plugins/ac-core` or `~/.hermes/plugins/ac-postgres` directory after checking that it does not already exist, then enable it. Git-installed plugins can be updated through `hermes plugins update`. Business-project knowledge must use a project-scoped installation as described in the Pro guide.

## OpenCode

OpenCode loads these standard skills and the constitution through its own project configuration. It does not install the Codex or Claude plugin package. Merge the following paths into the existing `opencode.json` of each intended project; do not overwrite unrelated configuration. Replace the absolute paths with the local Git clone. The PostgreSQL path is optional.

For OpenCode 1:

```json
{
  "instructions": ["/absolute/path/agent-constitution/plugins/core/hooks/constitution.md"],
  "skills": {
    "paths": [
      "/absolute/path/agent-constitution/plugins/core/skills",
      "/absolute/path/agent-constitution/plugins/postgres/skills"
    ]
  }
}
```

For OpenCode 2, use the same `instructions` field and its current array form for skills:

```json
{
  "instructions": ["/absolute/path/agent-constitution/plugins/core/hooks/constitution.md"],
  "skills": [
    "/absolute/path/agent-constitution/plugins/core/skills",
    "/absolute/path/agent-constitution/plugins/postgres/skills"
  ]
}
```

OpenCode 1.19.5 resolved the configuration, discovered the core, PostgreSQL, Pro and synthetic project skills, and delivered the constitution to main and subagent requests in an isolated test with a local model stub. The synthetic run explicitly allowed its `task` tool. OpenCode 2 syntax follows its [official skill documentation](https://opencode.ai/docs/skills/), but has not been tested here. Verify the selected skills and instructions in a new session. Project-specific knowledge and the Pro skill can be added as additional local skill paths.

## Cursor

Cursor reads `.cursor-plugin/marketplace.json` at the repository root. Cursor has no command for adding a
third-party marketplace from the terminal; it offers a team marketplace imported from a repository, and a
local plugin folder.

### Add the marketplace from GitHub (Teams and Enterprise)

Team marketplaces exist on Teams and Enterprise plans only, and on Enterprise only admins can add them
([source](https://cursor.com/docs/plugins#team-marketplaces)). To import this repository
([source](https://cursor.com/docs/plugins#add-a-team-marketplace)):

1. Open **Dashboard -> Plugins & MCPs**.
2. Under **Team Marketplaces**, click **Add Marketplace**.
3. Choose **Import from Repo** and paste `https://github.com/aprazdnikov/agent-constitution`.
4. Under **Marketplace Settings**, set **Marketplace Access** and save.

Then install the plugins in the editor
([source](https://cursor.com/docs/plugins#installing-plugins)):

1. Open **Customize** in the sidebar.
2. Find `core`, select **Install**, and choose project or user scope.
3. Optionally do the same for `postgres`.

### Use a local clone

Cursor loads plugins placed in `~/.cursor/plugins/local`. It skips symlinks that point outside that
folder, so copy the plugin directories rather than linking them
([source](https://cursor.com/docs/plugins#test-plugins-locally)):

```bash
mkdir -p ~/.cursor/plugins/local
cp -R agent-constitution/plugins/core ~/.cursor/plugins/local/core
cp -R agent-constitution/plugins/postgres ~/.cursor/plugins/local/postgres
```

The second `cp` is optional. Restart Cursor or run **Developer: Reload Window**, then check in
**Customize** that the skills appear
([source](https://cursor.com/docs/plugins#test-plugins-locally)). On Teams and Enterprise, this works
only when an admin allows local plugin imports, which is off by default on Enterprise
([source](https://cursor.com/docs/plugins#test-plugins-locally)).

### Confirm the hook ran

1. In the Cursor IDE, start a new Agent chat.
2. Ask: "Which rules and skills are active in this session?"
3. The answer should describe the Agent Constitution and its skill-routing list, naming
   `modify-existing-code`, `security-gate`, and, when `postgres` is installed, `postgres-migrations` and
   `postgres-pgbouncer`.

The session-start hook runs in the IDE only. Cursor cloud agents do not run `sessionStart` hooks
([source](https://cursor.com/docs/hooks#cloud-agent-support)), so a cloud agent sees the skills but not
the constitution that routes to them.

## Limitations

### Subagent context

The `core` plugin is designed to supply the constitution and skill routing when a subagent starts. In Claude Code, Codex and Qwen, `SubagentStart` returns context to the child; Codex requires the hook to be trusted. Local synthetic runs verified context delivery with Codex CLI 0.166.0, Claude Code 2.1.296 and Qwen Code 0.27.0, using a local model stub. Hermes 0.22.5 received its plugin system-prompt section in the main and subagent requests in the same kind of synthetic test. OpenCode 1.19.5 also delivered the configured instructions to a synthetic subagent. The coordinator receives instructions to pass relevant confirmed project context and constraints to subagents and review their work. A project plugin's own knowledge is not automatically copied by the `core` hook.

Cursor's `subagentStart` cannot inject context. `hooks/cursor-subagent.py` is an experimental `preToolUse` handler for `Task`; it prepends the constitution to the task prompt and requires Python 3. It is **not registered or enabled by default**. Multiple hooks may rewrite the same original task and one update can replace another, potentially losing a restriction or redaction supplied by another hook. Cursor's response schema and permission behavior also need end-to-end verification: an invalid permission-hook response can block `Task`, while a hook error may let a task proceed without the context. Test delivery and permission behavior in an isolated Cursor installation, including interactions with every other `Task` hook, before opting in. The coordinator is instructed to include relevant constraints in delegated tasks. Hooks do not replace permissions or sandbox restrictions.

Sources: [Codex hooks](https://learn.chatgpt.com/docs/hooks), [Claude Code hooks](https://code.claude.com/docs/en/hooks#subagentstart), [Cursor hooks](https://cursor.com/docs/hooks#pretooluse).

- **Windows is not supported for the hook yet.** Every agent starts the hook as `sh .../session-start.sh`,
  so it needs a POSIX `sh` on `PATH`. The skills themselves have no such requirement.
- **Updates arrive through each agent's own plugin update mechanism.** This repository has no updater of
  its own.
  - Claude Code: `claude plugin update core@agent-constitution`, and the same for `postgres`
    ([source](https://code.claude.com/docs/en/plugins/install#update-plugins-now)). Auto-update is off by
    default for third-party marketplaces; turn it on from the **Marketplaces** tab in `/plugin`
    ([source](https://code.claude.com/docs/en/plugins/install#keep-plugins-updated)). With a local-clone
    marketplace, changes in the clone apply at the next session start or after `/reload-plugins`
    ([source](https://code.claude.com/docs/en/plugins/create-marketplace#test-an-edit-to-a-plugin)).
  - Codex: `codex plugin marketplace upgrade agent-constitution` refreshes the Git marketplace and the
    installed plugins from it
    ([source](https://github.com/openai/codex/blob/7f892275e31002f0422477c6219189284560e689/codex-rs/cli/src/marketplace_cmd.rs#L95-L100)).
    It applies only to marketplaces added from Git; for a local-clone marketplace, see
    [openai/codex](https://github.com/openai/codex). If an update changes the hook entry, approve the hook
    again as described in [Approve the hook](#approve-the-hook).
  - Cursor: in a team marketplace, click **Refresh**, or turn on **Enable Auto Refresh** for a GitHub
    import ([source](https://cursor.com/docs/plugins#keep-plugins-up-to-date)). For a local copy, copy
    the plugin directories again and reload the window
    ([source](https://cursor.com/docs/plugins#test-plugins-locally)).
