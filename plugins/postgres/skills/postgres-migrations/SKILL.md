---
name: postgres-migrations
description: PostgreSQL schema migrations and DDL. Use when writing or reviewing a migration file or any DDL statement that will run against a PostgreSQL database with live traffic.
---

# PostgreSQL migrations

A migration is safe when it never holds a lock that blocks application traffic for longer than a few seconds and when the application versions running before, during and after the deploy all work against every intermediate schema. PostgreSQL holds every lock until the transaction ends, most `ALTER TABLE` forms take ACCESS EXCLUSIVE (which blocks even `SELECT`), and a waiting ACCESS EXCLUSIVE request blocks every later conflicting request on that table. This skill turns one risky statement into a sequence of short-lock steps.

Not in scope: tuning read-only queries, `EXPLAIN` analysis, or data changes with no DDL. If the request has no DDL and no migration file, stop and handle it without this skill.

## Workflow

1. **Inventory.** List each statement, the table it touches, the table's size and write rate, and the lock it takes (see [references/lock-levels.md](references/lock-levels.md)). Stop and ask if you cannot tell whether the table is large or busy; treat it as large.
2. **Find what the running code needs.** Search the application for every read and write of the columns, tables and constraints you change. If the currently deployed version uses something you remove or rename, switch to expand and contract (rule 7). Do not ship a breaking change in one step.
3. **Classify each statement.** Mark it as catalog-only, scan, or rewrite. Every scan or rewrite under ACCESS EXCLUSIVE or SHARE on a large table must be replaced by a rule below. Stop if no rule fits: say the change needs a maintenance window and why.
4. **Split into files.** One file per transactional unit. Statements using `CONCURRENTLY` go alone in a file that the runner does not wrap in a transaction. Validations and backfills go in their own steps after the cheap DDL is committed.
5. **Add timeouts to every file** (rule 1) and state the retry policy.
6. **Review the result.** For each file, answer: which lock, for how long, what does it block, what happens if it fails halfway. Stop and fix any file where an answer is "the whole scan" or "unknown".
7. **Report.** List the files in deploy order, which application release each one must precede or follow, and the manual check after any `CONCURRENTLY` step.

## Rules

### 1. Bound every lock wait and every statement

Set `lock_timeout` (a few seconds) and `statement_timeout` at the top of each migration with `SET LOCAL` inside a transaction, or `SET` in a non-transactional file. `lock_timeout` applies to each lock acquisition separately. On a timeout, the migration fails cleanly: retry it later with backoff, a bounded number of times. Never raise the timeout to make it pass. Do not set either in `postgresql.conf`, because that affects all sessions.

✅
```sql
BEGIN;
SET LOCAL lock_timeout = '3s';
SET LOCAL statement_timeout = '15s';
ALTER TABLE orders ADD COLUMN customer_id bigint;
COMMIT;
```
❌
```sql
ALTER TABLE orders ADD COLUMN customer_id bigint;  -- may wait forever and stall all queries on orders
```

### 2. Build and drop indexes concurrently

Plain `CREATE INDEX` takes SHARE and blocks all writes for the whole build; plain `DROP INDEX` takes ACCESS EXCLUSIVE. The `CONCURRENTLY` forms allow reads and writes but cannot run inside a transaction block, accept one index per statement, and do not work for indexes on partitioned tables (drop) or with `CASCADE`.

A failed concurrent build leaves an INVALID index that is ignored for reads but still slows writes and, if unique, still enforces uniqueness. After the step, check for it and drop it before retrying:

```sql
SELECT indexrelid::regclass FROM pg_index WHERE NOT indisvalid;
DROP INDEX CONCURRENTLY IF EXISTS orders_customer_id_idx;
```

✅
```sql
-- no-transaction
SET lock_timeout = '3s';
CREATE INDEX CONCURRENTLY IF NOT EXISTS orders_customer_id_idx ON orders (customer_id);
```
❌
```sql
BEGIN;
CREATE INDEX orders_customer_id_idx ON orders (customer_id);  -- blocks writes for the full build
COMMIT;
```

For a unique constraint or primary key, build the unique index concurrently, then attach it with `ADD CONSTRAINT ... UNIQUE USING INDEX` (or `PRIMARY KEY USING INDEX`), which is a short catalog change.

### 3. Add foreign keys as NOT VALID, then validate

`ADD FOREIGN KEY` takes SHARE ROW EXCLUSIVE on both tables and scans the referencing table. With `NOT VALID` the scan is skipped and new rows are checked at once. `VALIDATE CONSTRAINT` then scans under SHARE UPDATE EXCLUSIVE, which does not block reads or writes. Run it in a separate transaction.

✅
```sql
ALTER TABLE orders ADD CONSTRAINT orders_customer_fk
  FOREIGN KEY (customer_id) REFERENCES customers (id) NOT VALID;
-- next transaction or next migration
ALTER TABLE orders VALIDATE CONSTRAINT orders_customer_fk;
```
❌
```sql
ALTER TABLE orders ADD CONSTRAINT orders_customer_fk
  FOREIGN KEY (customer_id) REFERENCES customers (id);  -- full scan while writes are blocked
```

### 4. Reach NOT NULL through a validated constraint

`SET NOT NULL` scans the whole table under ACCESS EXCLUSIVE, unless a valid `CHECK` constraint already proves the column has no nulls. Add that check as `NOT VALID`, validate it, then `SET NOT NULL` (now catalog-only), then drop the check. On PostgreSQL 18 or later you may instead add `CONSTRAINT name NOT NULL col NOT VALID` and validate it. Backfill nulls first (rule 6).

✅
```sql
ALTER TABLE orders ADD CONSTRAINT orders_customer_id_nn
  CHECK (customer_id IS NOT NULL) NOT VALID;
-- separate transaction, so the scan does not run under the ADD's ACCESS EXCLUSIVE
ALTER TABLE orders VALIDATE CONSTRAINT orders_customer_id_nn;
-- separate transaction
ALTER TABLE orders ALTER COLUMN customer_id SET NOT NULL;
ALTER TABLE orders DROP CONSTRAINT orders_customer_id_nn;
```
❌
```sql
ALTER TABLE orders ALTER COLUMN customer_id SET NOT NULL;  -- full scan under ACCESS EXCLUSIVE
```

### 5. Know which column changes rewrite the table

Since PostgreSQL 11, `ADD COLUMN` with a non-volatile default (a constant, `now()`) only writes the catalog. A volatile default (`clock_timestamp()`, `random()`, `gen_random_uuid()`), a stored generated column, an identity column, or a domain with constraints rewrites the table and its indexes. `ALTER COLUMN TYPE` rewrites unless the old type is binary coercible to the new one and `USING` keeps values as they are: `varchar(n)` to `text` or to a larger `varchar` is free, `int` to `bigint` is a rewrite. For a rewrite on a large table, use expand and contract with a new column. More cases: [references/lock-levels.md](references/lock-levels.md).

✅
```sql
ALTER TABLE events ADD COLUMN source text NOT NULL DEFAULT 'web';
ALTER TABLE users ALTER COLUMN fullname TYPE text;  -- from varchar(100): no rewrite
```
❌
```sql
ALTER TABLE events ADD COLUMN token uuid NOT NULL DEFAULT gen_random_uuid();  -- rewrites the table
ALTER TABLE events ALTER COLUMN id TYPE bigint;  -- rewrites the table and every index
```

### 6. Backfill in bounded batches with a commit per batch

One `UPDATE` over a large table holds row locks on every touched row until it commits, bloats the table and replicates as one burst. Update a bounded key range or a `LIMIT`ed set per transaction, commit, pause, repeat until no rows change. Run the backfill outside the schema migration transaction, and make it restartable.

✅
```sql
-- repeat, one transaction each, until 0 rows updated
UPDATE orders SET customer_id = o.legacy_customer_id
FROM (SELECT id, legacy_customer_id FROM orders
      WHERE customer_id IS NULL ORDER BY id LIMIT 5000) o
WHERE orders.id = o.id;
```
❌
```sql
UPDATE orders SET customer_id = legacy_customer_id;  -- 80M rows in one transaction
```

### 7. Rename and drop with expand, migrate, contract

Old and new application versions run together during a deploy, so each schema state must serve both.

1. **Expand:** add the new column or table; nothing reads it yet.
2. **Migrate:** release code that writes both old and new (or add a trigger), backfill in batches, then release code that reads the new one.
3. **Contract:** after no deployed version touches the old name, drop it in a later release.

`RENAME COLUMN` and `DROP COLUMN` are fast but break any running code that still uses the old name, so they belong only in the contract step.

✅
```sql
-- release N
ALTER TABLE users ADD COLUMN display_name text;
-- release N+1 writes both, backfill runs, release N+2 reads display_name
-- release N+3
ALTER TABLE users DROP COLUMN fullname;
```
❌
```sql
ALTER TABLE users RENAME COLUMN fullname TO display_name;  -- old pods fail until rollout ends
```

## Sources

- https://www.postgresql.org/docs/current/explicit-locking.html
- https://www.postgresql.org/docs/current/sql-createindex.html
- https://www.postgresql.org/docs/current/sql-altertable.html
- https://www.postgresql.org/docs/current/runtime-config-client.html
- https://www.postgresql.org/docs/current/sql-dropindex.html
- https://www.postgresql.org/docs/current/sql-createtable.html
