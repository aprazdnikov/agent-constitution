---
name: modify-existing-code
description: Safe changes to an existing codebase. Use when changing code you did not write in the current session, such as bug fixes, features or refactors in an existing project.
---

# Modify existing code

Code you did not write has callers, tests and history you have not seen, and other people depend on its behavior in ways the file does not show. The goal of this skill is a change that does exactly what was asked, breaks nothing that was not meant to break, and leaves the user informed about everything else you noticed. It does not apply to files you create from scratch in this session, or to a project with no existing code: there is nothing to trace, so write the code directly.

## Workflow

1. **List the symbols you will touch.** Name every function, method, type, constant, flag, config key, column and endpoint the change will edit, rename or remove.

2. **Find every usage and every test of each symbol.** Search the whole repository, not only the file you were pointed to:
   - `git grep -n -w <symbol>` for exact word matches in tracked files; add `-F` when the name contains regex characters, and `-- <pathspec>` to narrow by path.
   - The language's reference tooling (LSP "find references", `go list`/`gopls`, an IDE index) for calls through interfaces, re-exports and dynamic dispatch that text search misses.
   - Search string forms too: config keys, CLI flag names, JSON field names, SQL column names, and reflection or registry lookups.
   - Name the tests that cover each symbol. If none exist, note it.

3. **Read the history when behavior is surprising.** If the current behavior looks wrong, odd or deliberate, find out why before changing it:
   - `git log -L :<funcname>:<file>` or `git log -L <start>,<end>:<file>` shows every commit that changed that function or range, with patches.
   - `git blame -L <start>,<end> <file>` shows the last commit per line; add `-w` to skip whitespace-only commits and `-C` to follow lines moved from other files.
   - Read the commit messages and linked issues. A comment like "use UTC for invoice cutoff" is intent, not an accident.

   **Stop:** if the existing behavior looks intentional and conflicts with the request, or you cannot tell whether it is intentional, ask the user which behavior they want before editing.

4. **Record the baseline.** Run the relevant existing tests (those found in step 2, plus the test suite of the touched package) before editing. Save the result: which pass, which fail, which are skipped. Failures that exist before your change are not yours, and you must be able to say so.

   **Stop:** if the change is risky (shared helper, money, auth, persistence, concurrency, many callers) and no test covers the behavior you are changing, tell the user and propose adding a characterization test first. Do not edit untested risky code on your own judgement.

5. **Check the public contract.** A contract is anything someone outside the edited file relies on: function and method signatures of exported symbols, wire formats (JSON fields, protobuf, HTTP routes and status codes), database schema, CLI flags and their meaning, config keys, environment variables, file formats, and documented error messages.

   **Stop:** if the request requires breaking a contract, do not just do it. Tell the user what breaks, who is affected (the usages from step 2), and a migration path such as a deprecated alias, a new flag next to the old one, or a versioned endpoint. Proceed only after the user chooses.

6. **Make the smallest diff that delivers the request.** Edit only the lines needed for the requested behavior. No renames, reformatting, import reordering, comment rewrites or refactors of code the change does not need. If the fix truly requires a refactor, say so and keep it in a separate, clearly described step.

7. **Collect out-of-scope findings instead of fixing them.** Bugs, smells, dead code or security issues you notice outside the requested change go into a list for the user, each with file, line and a one-line description. Do not fix them in this diff.

8. **Run the same tests again.** Compare with the baseline from step 4. Every test that passed before must still pass; any newly failing test is yours to fix or explain. Add or update tests that cover the new behavior.

9. **Report.** State the usages you checked, the baseline and final test results, any contract impact and its migration path, and the out-of-scope findings from step 7.

## Examples

### Find usages before editing

Before changing `to_report_date`, run `git grep -n -w to_report_date`, find callers in `reports/daily.py`, `billing/invoice.py` and `api/serializers.py`, and check how each one depends on the result.

### Read history before reversing behavior

`git log -L :to_report_date:billing/dates.py` shows a commit "use UTC for invoice cutoff"; ask the user whether invoices should keep UTC, or scope the fix to the report path.

### Record a baseline

Run `pytest tests/test_dates.py` before the edit (12 passed, 1 failing already), then after (13 passed), and report both.

### Stop on risky untested code

"`apply_discount` has no tests and is called from checkout. I propose adding a characterization test for current behavior first. Proceed?"

### Preserve contracts or announce the break

"Renaming `output_path` to `output_dir` breaks existing configs and `scripts/nightly.sh`. I suggest reading `output_path` as a deprecated alias with a warning. Should I do that?"

### Keep the diff to the request

A one-line fix to the date conversion; the rest of the file is untouched.

### Report out-of-scope problems

"Unrelated: `cmd/export.go:88` ignores the error from `file.Close()`. Not changed in this diff."

### Skip the workflow when there is no existing code

In an empty repository, asked to create `hello.py`, write the file and run it once.

## Sources

- git-grep, options `-n`, `-w`, `-F`, `-e` and `--` pathspec: https://git-scm.com/docs/git-grep
- git-log, option `-L <start>,<end>:<file>` and `-L :<funcname>:<file>`: https://git-scm.com/docs/git-log
- git-blame, options `-L`, `-w`, `-M`, `-C` and `--ignore-rev`: https://git-scm.com/docs/git-blame
