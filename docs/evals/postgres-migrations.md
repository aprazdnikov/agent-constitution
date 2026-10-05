# Evals: postgres-migrations

## Add a required foreign key and its index to a large table

**Kind:** positive

**Prompt:** "Our Rails-style service keeps plain SQL migrations in `db/migrations/NNNN_name.sql`; the runner wraps each file in a transaction unless the file starts with `-- no-transaction`. The `orders` table has about 80 million rows and takes writes all day. Add a `customer_id bigint` column that references `customers(id)`, must be NOT NULL, and needs an index. Write the migration(s)."

**Baseline failure:** The agent writes one transactional file containing `ADD COLUMN customer_id bigint NOT NULL REFERENCES customers(id)` and a plain `CREATE INDEX`. That fails on existing rows, or, given a default, validates the foreign key and builds the index while holding locks that block writes on `orders` for the whole scan. It sets no `lock_timeout`, so the ALTER can queue behind a long transaction and stall all traffic to the table.

**Pass criteria:**
- Every file that takes an ACCESS EXCLUSIVE or SHARE ROW EXCLUSIVE lock first runs `SET lock_timeout` (a few seconds at most) and `SET statement_timeout`, and the answer says to retry on lock timeout rather than raise the limit.
- The column is added as nullable with no volatile default.
- The foreign key is added with `NOT VALID` and validated with `VALIDATE CONSTRAINT` in a separate statement or migration.
- NOT NULL is reached either through `CHECK (customer_id IS NOT NULL) NOT VALID` + `VALIDATE` + `SET NOT NULL` (+ dropping the check) or through a `NOT NULL ... NOT VALID` constraint + `VALIDATE` on PostgreSQL 18 or later, after a batched backfill.
- The index is built with `CREATE INDEX CONCURRENTLY` in a file marked `-- no-transaction`, and the answer says how to detect and drop an INVALID index if the build fails.
- The backfill updates rows in bounded batches with a commit after each batch, not in one `UPDATE`.

## Rename a column used by the running application

**Kind:** positive

**Prompt:** "In our Go service (`migrations/` holds goose SQL files; we deploy with rolling restarts, so old and new pods run side by side for about ten minutes), rename `users.fullname` to `users.display_name` and change it from `varchar(100)` to `text`. Write the migration."

**Baseline failure:** The agent writes `ALTER TABLE users RENAME COLUMN fullname TO display_name` in a single migration that ships with the code change. Old pods still query `fullname` and fail with errors until the rollout finishes. It may also assume the type change rewrites the table and schedule unnecessary downtime, or the reverse for a type change that does rewrite.

**Pass criteria:**
- The answer splits the change into expand, migrate and contract steps across separate deploys: add `display_name`, write to both columns (or use a trigger), backfill in batches, switch reads, stop writing the old column, then drop `fullname` in a later release.
- No step removes or renames something that the currently deployed version still reads or writes.
- The answer states that `varchar(n)` to `text` is binary coercible and does not rewrite the table, and names at least one type change that does rewrite (for example `int` to `bigint`).
- Each DDL statement is preceded by `SET lock_timeout`.

## Speed up a slow reporting query (boundary negative)

**Kind:** negative

**Prompt:** "This dashboard query against our read replica takes 12 seconds: `SELECT date_trunc('day', created_at), count(*) FROM events WHERE tenant_id = $1 GROUP BY 1`. Here is the `EXPLAIN (ANALYZE, BUFFERS)` output. Why is it slow and how can I rewrite it? We cannot change the schema this quarter."

**Baseline failure:** None expected from the skill's absence; the risk is the opposite. An agent that loads the migration skill drifts into proposing new indexes, lock timeouts and migration files, which the user ruled out.

**Pass criteria:**
- The `postgres-migrations` skill is not loaded, or if loaded, it is put aside once it is clear that no DDL is requested.
- The answer works from the plan: query shape, filters, estimates versus actual rows, buffers, and rewrites of the SELECT itself.
- The answer contains no migration file, `SET lock_timeout`, `CREATE INDEX` or other DDL as the proposed fix.
