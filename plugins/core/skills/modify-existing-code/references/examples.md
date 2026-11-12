# Examples

## Shared behavior

Before changing `to_report_date`, find its callers in reports, billing and API serializers. Check their tests and use reference tooling to follow indirect calls. Inspect the relevant history if a UTC cutoff appears deliberate; preserve it or ask the developer when the requested behavior remains unclear.

## Focused baseline

Reproduce a date conversion bug with `pytest tests/test_dates.py` before editing and rerun the affected tests after the fix. Report any pre-existing failures separately.

## Compatibility

When renaming `output_path` would affect existing configurations, identify their consumers and support a deprecated alias where practical. If the desired migration is unclear, describe the impact and ask the developer; if an incompatible change and its impact were already approved, implement and report them.

## Sources

- Git search: https://git-scm.com/docs/git-grep
- Git history: https://git-scm.com/docs/git-log
- Git attribution: https://git-scm.com/docs/git-blame
