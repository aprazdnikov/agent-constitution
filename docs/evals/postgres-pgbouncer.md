# Evals: postgres-pgbouncer

## Per-request tenant setting behind a transaction pooler

**Prompt:** "Our Python API uses row-level security keyed on `app.tenant_id`. Add a request middleware that sets the tenant for the current request before the handlers run their queries." Repository: FastAPI service, `deploy/pgbouncer.ini` contains `pool_mode = transaction`, and `DATABASE_URL` points at port 6432.

**Baseline failure:** The agent runs `SET app.tenant_id = '...'` (or `set_config('app.tenant_id', ..., false)`) once at the start of the request on a pooled connection, then lets each handler query run in its own autocommit transaction. The setting stays on whichever server connection ran the `SET`, so later queries can run without it or with another tenant's value.

**Pass criteria:** The agent reads `pool_mode` from `deploy/pgbouncer.ini` and says the project uses transaction pooling. The generated code opens one explicit transaction per request (or per unit of work), sets the tenant with `SET LOCAL` or `set_config('app.tenant_id', $1, true)` inside that transaction, and runs the handler queries in the same transaction. No session-level `SET` or `set_config(..., false)` appears in the diff.

## Singleton job lock and cache invalidation listener

**Prompt:** "Make the nightly `rebuild_reports` job safe to run on several workers at once: only one worker should do the work. Also add a listener that clears the in-process cache when a `cache_invalidate` notification arrives." Repository: Node.js worker, connects through PgBouncer; the pooler config is not in the repository and the README says nothing about pool mode.

**Baseline failure:** The agent calls `pg_advisory_lock(key)` and later `pg_advisory_unlock(key)` as separate statements through the pool, and runs `LISTEN cache_invalidate` on a pooled connection. Under transaction pooling the unlock can reach a different server connection, so the lock leaks until that server connection closes, and the listener silently receives nothing.

**Pass criteria:** The agent states that the pool mode is unknown, asks the user or says it is assuming transaction mode, and proceeds on that assumption. The lock uses `pg_try_advisory_xact_lock` (or `pg_advisory_xact_lock`) with the whole job's database work inside that one transaction, or the agent explains why the job is too long for one transaction and proposes a dedicated direct (non-pooled) connection. The `LISTEN` code uses a connection that bypasses the transaction pooler (direct to Postgres or a session-mode pool), and the agent names that connection requirement explicitly. `NOTIFY` senders are left on the pooled connection.

## Boundary: direct connection without a pooler

**Prompt:** "Add a `statement_timeout` of 5 seconds for the reporting module's database session and use a session advisory lock so only one report export runs at a time." Repository: Go service with `DATABASE_URL=postgres://app@db.internal:5432/app`; `docker-compose.yml` runs only `postgres:16`; no PgBouncer config, image, or dependency anywhere.

**Baseline failure:** None expected from this skill; the risk is a false trigger: an agent loaded with pooling rules rewrites the code to `SET LOCAL` and transaction-scoped locks, or refuses session features, although nothing pools the connection.

**Pass criteria:** The agent checks for a pooler, finds none (port 5432, no PgBouncer service or config), and does not apply transaction-pooling restrictions. It may use session-level `SET` and `pg_advisory_lock`/`pg_advisory_unlock` on a dedicated connection. It does not claim the code is unsafe because of PgBouncer.
