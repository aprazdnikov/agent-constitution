---
name: postgres-pgbouncer
description: PostgreSQL access through PgBouncer transaction pooling. Use when writing or reviewing application code or SQL that connects to Postgres through PgBouncer in transaction (or statement) pooling mode, or when the pool mode of a PgBouncer in front of the database is unknown.
---

# PgBouncer transaction pooling

In transaction pooling, PgBouncer hands a client a server connection only for the duration of one transaction and returns it to the pool when the transaction ends. The next transaction from the same client can run on a different server connection that another client used a moment ago. Anything that lives in the server *session* rather than in the *transaction* therefore either vanishes, leaks to another client, or cannot be cleaned up. This skill makes the agent find out which pool mode is in use and, under transaction pooling, keep all state transaction-scoped.

## Workflow

1. **Find the pooler.** Look for `pgbouncer.ini`, a PgBouncer container or Helm chart, connection strings, and deployment docs.
   - No pooler anywhere and the connection string targets Postgres directly: **stop**, this skill does not apply. Session features are fine.
2. **Determine the pool mode.**
   - In `pgbouncer.ini`, read `pool_mode` in `[pgbouncer]`, then check for per-database overrides (`pool_mode=` in a `[databases]` entry) and per-user overrides (`[users]`). The most specific one wins for that connection. If no `pool_mode` is set at all, the default is `session`.
   - Port `6432` is PgBouncer's default `listen_port`. It hints that a pooler is present; it does not tell you the mode.
   - Config not in the repository (managed pooler, separate infra repo): ask the user which mode the connection uses.
   - Mode is `session` for every connection this code uses: **stop**, apply no restrictions.
   - Mode is `transaction` or `statement`, or still unknown after asking: continue, and **say in your answer that you are assuming transaction mode** when you could not confirm it.
3. **Scan the code you are writing or changing** for every construct in the rules below, including what the database driver does implicitly (rule 8).
4. **Rewrite each hit** to its transaction-scoped form. When a feature truly needs a session (a long-lived `LISTEN`, a lock held across many transactions), route that one piece of code through a connection that bypasses the transaction pooler — a direct Postgres connection or a session-mode pool — and name that connection requirement explicitly to the user. Do not invent the address; ask for it or reuse one already defined in the project.
5. **Under statement mode**, additionally make sure no code relies on multi-statement transactions: PgBouncer disallows them there. If it does, **stop** and tell the user the pool mode must change for this code path.
6. **Report**: the pool mode and where you found it (or that you assumed it), each construct you replaced, and any connection that must bypass the pooler.

## Rules

PgBouncer's feature table lists these as never working in transaction mode: `SET`/`RESET`, `LISTEN`, `WITH HOLD` cursors, `PREPARE`/`DEALLOCATE`, temp tables with `PRESERVE ROWS` or `DELETE ROWS`, `LOAD`, and session-level advisory locks.

### 1. Settings: `SET LOCAL` inside an explicit transaction

A plain `SET` (same as `SET SESSION`) persists for the rest of the server session once committed — on a pooled connection that means it can apply to a different client, and your next transaction may not see it. `SET LOCAL` lasts until the transaction ends, committed or not. Outside a transaction block `SET LOCAL` only emits a warning and does nothing, so open the transaction first. `set_config(name, value, true)` is the function form of `SET LOCAL`; `false` makes it session-wide.

❌
```sql
SET statement_timeout = '5s';
SELECT * FROM report_rows WHERE ...;   -- may run on another server connection
```
✅
```sql
BEGIN;
SET LOCAL statement_timeout = '5s';
SELECT set_config('app.tenant_id', $1, true);
SELECT * FROM report_rows WHERE ...;
COMMIT;
```

Exception: PgBouncer tracks a fixed set of startup parameters (`client_encoding`, `DateStyle`, `IntervalStyle`, `TimeZone`, `standard_conforming_strings`, `application_name`) per client; more can be added with `track_extra_parameters`. Pass those as connection startup parameters, not via `SET`.

### 2. Advisory locks: transaction-level functions

A session-level advisory lock is held until explicitly unlocked or the session ends. Through a transaction pooler the unlock may hit a different server connection, so the lock leaks for as long as the server connection lives. `pg_advisory_xact_lock` / `pg_try_advisory_xact_lock` are released automatically at transaction end and cannot be released early — put all the protected work in that same transaction.

❌
```sql
SELECT pg_advisory_lock(42);
-- ... job runs in several transactions ...
SELECT pg_advisory_unlock(42);
```
✅
```sql
BEGIN;
SELECT pg_try_advisory_xact_lock(42);  -- false: another worker has it, ROLLBACK and exit
-- ... all of the job's writes ...
COMMIT;                                -- lock released here
```
If the work cannot fit in one transaction, use a direct connection for the lock holder (workflow step 4).

### 3. `LISTEN`: dedicated non-pooled connection

A listener registers on one server session; after the transaction ends PgBouncer may give that server to someone else and your client stops receiving notifications. `NOTIFY` itself works in transaction mode.

❌ `pool.query("LISTEN cache_invalidate")` on the pooled connection.
✅ A single long-lived client connected directly to Postgres (or through a session-mode pool) runs `LISTEN`; senders keep using the pool for `NOTIFY` or `pg_notify(...)`.

### 4. Cursors: `WITHOUT HOLD`, consumed in one transaction

A `WITH HOLD` cursor outlives its transaction on the server session that created it; your next fetch may not reach that server.

❌
```sql
DECLARE c CURSOR WITH HOLD FOR SELECT ...; COMMIT;
FETCH 100 FROM c;
```
✅
```sql
BEGIN;
DECLARE c CURSOR FOR SELECT ...;
FETCH 100 FROM c;  -- repeat until done
COMMIT;
```
For batch processing across transactions, use keyset pagination (`WHERE id > $last ORDER BY id LIMIT n`) instead of a held cursor.

### 5. Temporary tables: `ON COMMIT DROP`, used in one transaction

Temp tables with the default `PRESERVE ROWS` or with `DELETE ROWS` stay on a server session that later belongs to another client, and the next transaction may not find them.

❌
```sql
CREATE TEMP TABLE staging (LIKE orders);
COPY staging FROM STDIN;      -- separate autocommit transactions
INSERT INTO orders SELECT * FROM staging;
```
✅
```sql
BEGIN;
CREATE TEMP TABLE staging (LIKE orders) ON COMMIT DROP;
COPY staging FROM STDIN;
INSERT INTO orders SELECT * FROM staging;
COMMIT;
```

### 6. SQL-level `PREPARE`/`EXECUTE`/`DEALLOCATE`: do not use

PgBouncer forwards SQL-level prepared statement commands straight to whichever server connection is current, so `EXECUTE` can land on a server connection where the statement was never prepared, or where another client prepared a different statement under the same name. `max_prepared_statements` does not cover them.

❌
```sql
PREPARE find_user(int) AS SELECT * FROM users WHERE id = $1;
EXECUTE find_user(7);
```
✅ Send a parameterized query through the driver (`SELECT * FROM users WHERE id = $1` with bound parameters), and let rule 8 decide whether the driver may prepare it at protocol level.

### 7. `LOAD`: not through the pooler

`LOAD` affects only the server session that runs it.

❌ `LOAD 'auto_explain';` from application code on a pooled connection.
✅ Have the library loaded by server configuration (owned by the DBA or infrastructure), or run `LOAD` on a direct connection for a one-off debugging session.

### 8. Driver prepared-statement caches: match the PgBouncer version

Many drivers prepare statements at the protocol level and cache them per connection, without any SQL `PREPARE` in your code. PgBouncer supports protocol-level named prepared statements in transaction mode only when `max_prepared_statements` is non-zero. That setting was introduced in PgBouncer 1.21.0 (default `0`, off); since 1.24.0 the default is `200`.

- PgBouncer ≥ 1.21 with `max_prepared_statements > 0`: protocol-level prepared statements are safe; leave the driver's cache on.
- Older PgBouncer, or the setting is `0` or unknown: disable or bypass the driver's server-side prepared statement cache. The option name differs by driver — **check your driver's documentation**; do not guess a flag name.

❌ Assuming the driver default is safe without checking the PgBouncer version and `max_prepared_statements`.
✅ "PgBouncer is 1.23 with `max_prepared_statements = 100` in `pgbouncer.ini`, so the driver's prepared statement cache stays enabled." Or: "Version unknown; I disabled the driver's server-side statement cache per its documentation — re-enable once `max_prepared_statements` is confirmed non-zero."

Driver features that keep other session state (session-level `SET` on connect, connection "init" queries, session-scoped locks in migration tools) fall under rules 1–2: check the driver or tool documentation for what it runs on connect.

## Sources

- PgBouncer features (pool modes, SQL feature compatibility table): https://www.pgbouncer.org/features.html
- PgBouncer configuration (`pool_mode`, `max_prepared_statements`, `listen_port`, `track_extra_parameters`): https://www.pgbouncer.org/config.html
- PgBouncer changelog (1.21.0 prepared statement support, 1.24.0 default change): https://www.pgbouncer.org/changelog.html
- PostgreSQL `SET` (`SET LOCAL` vs `SET SESSION`): https://www.postgresql.org/docs/current/sql-set.html
- PostgreSQL administration functions (`set_config`, advisory locks): https://www.postgresql.org/docs/current/functions-admin.html
