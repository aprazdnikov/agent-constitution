# Threat classes: what to check

Category names follow OWASP Top 10:2025; CWE names follow the CWE list (2025 Top 25 rank in brackets where the entry is on it). "Mapped" means the CWE appears in that OWASP category's list of mapped CWEs.

## Injection

- **IDs:** A05:2025 - Injection. CWE-89 SQL Injection [#2], CWE-78 OS Command Injection [#9], CWE-77 Command Injection [#23], CWE-94 Code Injection [#10], CWE-79 Cross-site Scripting [#1]. Template injection is CWE-1336 (Improper Neutralization of Special Elements Used in a Template Engine); it is not in A05's mapped list but is fixed the same way.
- **Look for:** string concatenation or interpolation into SQL, shell commands, `eval`/`exec`, template source, LDAP/XPath queries, HTML output; `shell=True`, `os.system`, backticks; ORM "raw" escape hatches; user input used as an identifier (column, table, sort key).
- **Fix:** bound parameters; argument vectors without a shell; allow-lists for identifiers; render user data as template variables, never as template text; context-aware output encoding.

## Broken authentication and authorization

- **IDs:** A01:2025 - Broken Access Control (CWE-862 Missing Authorization [#4], CWE-863 Incorrect Authorization [#17], CWE-639 Authorization Bypass Through User-Controlled Key [#24], CWE-284 Improper Access Control [#19], CWE-352 CSRF [#3]); A07:2025 - Authentication Failures (CWE-306 Missing Authentication for Critical Function [#21]).
- **Look for:** new routes, handlers, jobs or RPC methods without an authentication guard; object IDs taken from the request and loaded without an ownership or tenant check; role checks done only in the UI; state-changing GET requests; session or token handling written by hand.
- **Fix:** deny by default; check authorization on the server for every object access; scope queries by the caller's tenant or owner; reuse the framework's auth and CSRF mechanisms.

## Secrets in code, logs and configuration

- **IDs:** CWE-798 Use of Hard-coded Credentials (mapped to A07:2025 - Authentication Failures); CWE-321 Use of Hard-coded Cryptographic Key (A04:2025 - Cryptographic Failures); CWE-532 Insertion of Sensitive Information into Log File (A09:2025 - Security Logging and Alerting Failures); CWE-200 Exposure of Sensitive Information to an Unauthorized Actor [#20] (A01:2025).
- **Look for:** literals that look like keys, tokens, passwords or connection strings; secrets in example configs, fixtures, Dockerfiles, CI files; logging of whole request objects, headers, bodies, exceptions with locals, or environment dumps; secrets returned in error messages.
- **Fix:** read secrets from the environment or a secret store; log an allow-list of fields; redact `Authorization`, cookies, tokens and personal data. A secret already committed must be rotated; deleting the line is not enough.

## Path traversal and unsafe file handling

- **IDs:** A01:2025 - Broken Access Control. CWE-22 Path Traversal [#6]; CWE-434 Unrestricted Upload of File with Dangerous Type [#12] (mapped to A06:2025 - Insecure Design).
- **Look for:** file paths built from request data, archive entry names (zip slip), symlinks; uploads stored under the web root or with the client's filename and extension; temp files with predictable names.
- **Fix:** resolve the final path and require it to stay under the resolved base directory; generate server-side file names; check type by content and allow-list; store uploads outside anything that executes or serves them.

## Server-side request forgery

- **IDs:** A01:2025 - Broken Access Control. CWE-918 Server-Side Request Forgery (SSRF) [#22].
- **Look for:** HTTP clients, URL fetchers, webhooks, image or PDF renderers, XML parsers with external entities, any place a user-influenced URL or host is requested by the server.
- **Fix:** allow-list schemes and hosts; resolve the host and reject private, loopback, link-local and metadata addresses; do not follow redirects blindly; enforce the check on the address actually connected to.

## Unsafe deserialization

- **IDs:** A08:2025 - Software or Data Integrity Failures. CWE-502 Deserialization of Untrusted Data [#15].
- **Look for:** `pickle`, `marshal`, `yaml.load` without a safe loader, Java native serialization, `BinaryFormatter`, PHP `unserialize`, polymorphic JSON type handling, on data from a network, queue, cache, cookie or user file.
- **Fix:** plain data formats (JSON) parsed into explicit schemas; safe loaders; sign and verify data that must round-trip through an untrusted party.

## Resource exhaustion

- **IDs:** CWE-770 Allocation of Resources Without Limits or Throttling [#25]; CWE-1333 Inefficient Regular Expression Complexity. Neither is in the mapped list of an OWASP Top 10:2025 category; cite the CWE alone.
- **Look for:** request bodies, uploads, decompression, pagination and batch sizes with no upper bound; loops or recursion driven by input size or depth; nested quantifiers such as `(a+)+` applied to untrusted text; missing timeouts on outbound calls; unbounded queues, caches or thread pools.
- **Fix:** explicit size, count, depth and time limits; server-side page size caps; linear-time regex engines or bounded input length; timeouts everywhere; rate limits on expensive operations.

## Vulnerable or untrusted dependencies

- **IDs:** A03:2025 - Software Supply Chain Failures. CWE-1395 Dependency on Vulnerable Third-Party Component; CWE-1104 Use of Unmaintained Third Party Components.
- **Look for:** new or upgraded packages, unpinned versions, missing lock file updates, packages with names close to popular ones, install scripts, downloads piped to a shell, CI actions referenced by mutable tag.
- **Fix:** pin and lock; prefer maintained, widely used packages; check advisories for the chosen version; pin CI actions to a commit; verify checksums of downloaded artifacts.

## Defaults and configuration

- **IDs:** A02:2025 - Security Misconfiguration; A04:2025 - Cryptographic Failures.
- **Look for:** debug mode, permissive CORS, disabled TLS verification, weak or default credentials, verbose error pages, new feature flags that default to the unsafe state, fail-open error handling.
- **Fix:** secure value as the default, unsafe value only by explicit, environment-scoped opt-in; fail closed.
