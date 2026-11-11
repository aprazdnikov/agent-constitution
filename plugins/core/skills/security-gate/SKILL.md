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
- When nothing significant is found, the section holds exactly this sentence: "No exploitable weakness found in the inputs, defaults, or logging touched by this change."

Do not pad the section with generic advice that is not tied to the change.

## Rules with examples

### Bind parameters; never build queries from input (CWE-89)

```python
cur.execute("SELECT * FROM reports WHERE owner_id = ?", (owner,))
```

### Pass argument lists; never hand input to a shell (CWE-78)

```python
subprocess.run(["convert", "--", name, "out.png"], check=True)
```

### Check ownership of every object fetched by ID (CWE-639)

```python
report = Report.get(id=request.args["id"], owner_id=current_user.id)
if report is None:
    abort(404)
```

### Keep resolved paths inside the base directory (CWE-22)

```python
base = Path(REPORTS_DIR).resolve()
path = (base / name).resolve()
if not path.is_relative_to(base):
    abort(404)
return send_file(path)
```
If an attacker can change directory entries concurrently, use descriptor-relative file access that prevents symlink traversal; a path check alone does not prevent a race.

### Read secrets from the environment and keep them out of logs (CWE-798, CWE-532)

```python
API_KEY = os.environ["API_KEY"]
log.info("sent status=%s id=%s", resp.status_code, request_id)
```

### Allow-list outbound destinations (CWE-918)

Require HTTPS and an approved hostname. Validate all resolved addresses as publicly routable, rejecting loopback, private, link-local and metadata addresses. Connect to a validated address while verifying TLS against the original hostname; disable redirects or validate each destination the same way. Enforce the same restrictions at network egress where possible.

### Parse untrusted data as plain data (CWE-502)

```python
job = JobSchema.model_validate_json(message.body)
```

### Bound every input-driven cost (CWE-770, CWE-1333)

```python
limit = max(1, min(int(request.args.get("limit", 50)), 200))
if len(text) > 1000:
    abort(413)
re.fullmatch(r"[\w\s]+", text)
```

### Keep verification on; scope exceptions explicitly (A04:2025, A02:2025)

```python
requests.post(url, json=payload, verify=settings.CA_BUNDLE or True)
```
`CA_BUNDLE` points at the staging CA in staging only and is unset elsewhere.

## Sources

- OWASP Top 10:2025, https://owasp.org/Top10/ (redirects to https://top10.owasp.org/2025/): A01:2025 - Broken Access Control, A02:2025 - Security Misconfiguration, A03:2025 - Software Supply Chain Failures, A04:2025 - Cryptographic Failures, A05:2025 - Injection, A06:2025 - Insecure Design, A07:2025 - Authentication Failures, A08:2025 - Software or Data Integrity Failures, A09:2025 - Security Logging and Alerting Failures, A10:2025 - Mishandling of Exceptional Conditions.
- 2025 CWE Top 25 Most Dangerous Software Weaknesses, https://cwe.mitre.org/top25/ (list at https://cwe.mitre.org/top25/archive/2025/2025_cwe_top25.html).
- CWE entries outside the Top 25: https://cwe.mitre.org/data/definitions/798.html, https://cwe.mitre.org/data/definitions/532.html, https://cwe.mitre.org/data/definitions/1333.html, https://cwe.mitre.org/data/definitions/1336.html, https://cwe.mitre.org/data/definitions/1395.html.
