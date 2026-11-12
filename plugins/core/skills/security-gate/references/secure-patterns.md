# Secure implementation patterns

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
