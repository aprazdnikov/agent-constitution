---
name: security-gate
description: Security check for code changes and designs. Use when doing any programming task, including implementation, code review, refactoring or architecture design.
---

# Security gate

Every change to code or design can open a hole that tests will not show. This skill makes the agent check the work it produces or reviews against a fixed set of threat classes, fix what it finds within the task's scope, name what it leaves open, and report the result in a closing section the user can scan. It does not apply to answers that write, review or design no code, such as a question about git commands or tool usage.

## Workflow

1. **Decide whether the gate applies.** It applies when the answer writes, changes, reviews or designs code, configuration, infrastructure or dependencies. If nothing of that kind is produced or examined, stop here: no analysis, no closing section.
2. **List the entry points.** Find every external input the change touches: HTTP parameters, headers, cookies, bodies, file contents and names, environment variables, CLI arguments, queue messages, database rows written by other users, responses from other services, and values from tenants or admins. Treat all of them as attacker-controlled unless the code proves otherwise.
3. **Trace each input to its sinks.** Follow the value from where it enters to every place it is used: a query, a shell, a template, a file path, an outbound URL, a deserializer, a loop bound or allocation size, an authorization decision. At each sink, check the threat classes in [references/threat-classes.md](references/threat-classes.md): injection, broken authentication and authorization, secrets, path traversal and file handling, SSRF, unsafe deserialization, resource exhaustion, vulnerable dependencies.
4. **Check defaults and configuration.** For every new setting, flag or parameter, ask what happens when it is left unset. The unset state must be the safe one. Look for disabled TLS verification, debug modes, permissive CORS, default credentials and error paths that fail open.
5. **Check what the change logs and returns.** Read each new log call, error message and API response. Secrets, tokens, session identifiers, full headers or request bodies, and personal data must not appear.
6. **Check dependencies.** For each added or upgraded package, check that it is pinned, maintained and free of known advisories for that version, and that it is the package actually intended.
7. **Handle each finding.** Record: the weakness with its CWE ID and OWASP category; the impact if exploited; how exploitable it is (who can reach it, with what access, how hard). Then either fix it inside the current change, or, if the fix is out of scope, state the residual risk and why it is acceptable for now.
8. **Confirm security-sensitive actions.** Before changing permissions, handling credentials, exposing data, or taking another security-sensitive action, explain the specific action and ask the developer to approve it if they have not already authorized it. Do this even if local settings permit the action; do not expand local permissions. If an action weakens a control (disable certificate checks, skip an auth check, widen permissions, log a secret, accept any upload), explain what is lost, offer a safer alternative, and wait for the user's explicit decision. Record an accepted weaker control as residual risk.
9. **Write the closing section.** End the answer with the section described below.

## Closing section

Every answer the gate applies to ends with a section headed exactly `## Security check`.

- When there are findings, list each one: weakness and ID, impact, exploitability, and "fixed in this change" or "residual risk: <reason it is acceptable>".
- When nothing significant is found, say: "No significant security issue found in the reviewed changes."
- State any material limits on the security review; do not imply that unexamined behavior is safe.

Do not pad the section with generic advice that is not tied to the change.

For implementation patterns and sources, consult [references/secure-patterns.md](references/secure-patterns.md) when needed for the affected code.
