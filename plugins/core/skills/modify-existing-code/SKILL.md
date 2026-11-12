---
name: modify-existing-code
description: Safe changes to an existing codebase. Use when changing code you did not write in the current session, such as bug fixes, features or refactors in an existing project.
---

# Modify existing code

Deliver the requested change while protecting behavior that callers rely on. Adjust investigation and verification to the scope and risk of the change; follow project-specific requirements and the user's explicit instructions.

## Workflow

1. **Understand the affected behavior.** Identify the code, relevant project rules, existing tests and contracts touched by the request. Read related code and documentation needed to decide what must change. For a small local edit, keep the investigation local when its effects are clear.
2. **Trace impact.** For shared, exported, uncertain or widely used behavior, find callers and tests across the repository. Include interfaces, re-exports and dynamic dispatch; search string forms of flags, config keys, wire fields and database names as applicable. Use the project's reference tools when available. For unexpected or apparently deliberate behavior, inspect relevant history and decisions. Ask the developer when the intended behavior remains materially ambiguous.
3. **Establish a baseline when it matters.** For a bug, reproduce it or run a focused regression check when feasible. For risky or uncertain behavior, run relevant existing tests before editing and note pre-existing failures. If risky behavior has no coverage, add a characterization or regression test first when feasible; if its intended behavior cannot be established, explain the gap and ask the developer how to proceed.
4. **Protect contracts.** Consider public signatures, wire and file formats, schemas, CLI flags, configuration and documented errors. Preserve compatibility when practical. If the intended compatibility is unclear, explain affected consumers and a migration path and ask the developer; if the breaking impact was already explicitly authorized, implement it without asking again and report the impact.
5. **Make the requested change.** Keep the diff focused. Preserve project conventions, applicable security controls and required checks. Record unrelated findings for the developer instead of expanding the task without authorization.
6. **Verify and report.** Run focused tests or checks appropriate to the change, adding coverage for new or repaired behavior. Run broader suites when project policy, risk or failures warrant them. Repeat checks when later edits or unresolved concerns justify it. Report what changed, tests and their results, any contract impact, material verification limits and relevant out-of-scope findings.

For examples of tracing callers, investigating history and handling contracts, see [references/examples.md](references/examples.md) when needed.
