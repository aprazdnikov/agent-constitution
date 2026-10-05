# Installing Agent Constitution

This repository is a plugin marketplace named `agent-constitution`. It ships two plugins:

| Plugin | What it adds |
| :- | :- |
| `core` | A session-start hook that loads a short constitution into every new session, plus the skills `modify-existing-code` and `security-gate`. |
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
   `security-gate`, and database work to `postgres-migrations` and `postgres-pgbouncer`. Without
   `postgres`, the agent should say those two rows are unavailable.

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
