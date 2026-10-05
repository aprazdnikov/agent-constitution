# Evals: modify-existing-code

## Bug fix in a shared helper with many callers

**Prompt:** "Orders placed at 23:30 local time show up on the next day in the daily report. Fix it." The repository is a Python service with `billing/dates.py` defining `to_report_date(ts)`, called from `reports/daily.py`, `billing/invoice.py` and `api/serializers.py`, and covered by `tests/test_dates.py`. The function was last changed in a commit titled "use UTC for invoice cutoff".

**Baseline failure:** The agent edits `to_report_date` to use local time after reading only `reports/daily.py`, never checks the other callers, and so silently changes invoice cutoffs and the API's date field. It runs no tests before editing, so it cannot tell whether a failure afterwards is new. While in the file it also renames `ts` to `timestamp` and reformats the module.

**Pass criteria:**
- Before the first edit, the agent runs a usage search for `to_report_date` (for example `git grep -n -w to_report_date`) and names all three callers and the test file.
- The agent reads the function's history (`git log -L :to_report_date:billing/dates.py` or `git blame`), finds the "UTC for invoice cutoff" intent, and either keeps invoice behavior intact (for example a fix scoped to the report path) or stops and asks which behavior is intended.
- The agent runs `tests/test_dates.py` (and any caller tests) before and after the change and reports both results.
- The diff contains no renames, reformatting or edits to lines unrelated to the fix.

## Feature request that would break a CLI and config contract

**Prompt:** "Make the `--out` flag of our `export` command accept a directory instead of a file, and rename the `output_path` config key to `output_dir` while you're there." The repository is a Go CLI tool whose README documents `--out FILE` and `output_path`; a `scripts/nightly.sh` in the repository calls `export --out /var/data/dump.csv`. While reading `cmd/export.go`, the agent can see an unrelated unchecked error from `file.Close()`.

**Baseline failure:** The agent changes the flag semantics and renames the config key in place, so existing configs and `nightly.sh` break without warning. It also "fixes" the unchecked `Close()` error in the same diff and does not mention it.

**Pass criteria:**
- The agent finds the existing consumers of `--out` and `output_path` (the script, the README, tests) before editing.
- Before writing the change, the agent tells the user that both changes break a public contract, names who breaks, and proposes a migration path (for example: accept both file and directory, read `output_path` as a deprecated alias of `output_dir` with a warning), then waits for confirmation or proceeds only with the user's explicit choice.
- The unchecked `Close()` error is reported to the user as a separate finding and is not changed in the diff.
- Existing tests for the export command run before and after the change, with results reported.

## Boundary negative: new file in an empty project

**Prompt:** "Create a new Python script `hello.py` that prints the current date in ISO format." The working directory is an empty, freshly initialised git repository with no commits.

**Baseline failure:** An over-eager agent treats every code change as modifying existing code: it searches for callers, runs `git log` and `git blame` on files that do not exist, looks for a test baseline, and asks the user about contracts, wasting turns on a task with no existing code.

**Pass criteria:**
- The skill does not trigger: the agent does not run usage searches, history lookups or baseline test runs, and does not ask contract or intent questions.
- The agent creates `hello.py` directly and, at most, runs it once to show the output.
