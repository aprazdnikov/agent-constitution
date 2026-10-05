# Lock levels for common DDL

Source: PostgreSQL 18 documentation, [Explicit Locking](https://www.postgresql.org/docs/current/explicit-locking.html), [ALTER TABLE](https://www.postgresql.org/docs/current/sql-altertable.html), [CREATE INDEX](https://www.postgresql.org/docs/current/sql-createindex.html), [DROP INDEX](https://www.postgresql.org/docs/current/sql-dropindex.html).

`ALTER TABLE` takes ACCESS EXCLUSIVE unless the documentation for that subform says otherwise. A lock is held until the transaction ends, so a cheap statement inside a long transaction holds its lock for the whole transaction.

| Statement | Lock on the table | Blocks | Scans or rewrites? |
|---|---|---|---|
| `SELECT` | ACCESS SHARE | only ACCESS EXCLUSIVE | n/a |
| `INSERT` / `UPDATE` / `DELETE` / `MERGE` | ROW EXCLUSIVE | SHARE and stronger | n/a |
| `CREATE INDEX` | SHARE | all writes (reads continue) | full scan |
| `CREATE INDEX CONCURRENTLY` | SHARE UPDATE EXCLUSIVE | other DDL, VACUUM, another concurrent build; not reads or writes | two scans plus waits |
| `DROP INDEX` | ACCESS EXCLUSIVE | everything, including reads | no |
| `DROP INDEX CONCURRENTLY` | waits for conflicting transactions instead of locking them out | reads and writes continue | no |
| `ALTER TABLE ... ADD COLUMN` (nullable, or non-volatile default) | ACCESS EXCLUSIVE | everything | catalog only |
| `ALTER TABLE ... ADD COLUMN` (volatile default, stored generated, identity, constrained domain) | ACCESS EXCLUSIVE | everything | full rewrite of table and indexes |
| `ALTER TABLE ... ALTER COLUMN SET DEFAULT` / `DROP DEFAULT` | ACCESS EXCLUSIVE | everything | no; existing rows unchanged |
| `ALTER TABLE ... ALTER COLUMN TYPE` | ACCESS EXCLUSIVE | everything | rewrite unless binary coercible and `USING` leaves values unchanged; indexes may still rebuild |
| `ALTER TABLE ... SET NOT NULL` | ACCESS EXCLUSIVE | everything | full scan, skipped if a valid `CHECK (col IS NOT NULL)` exists |
| `ALTER TABLE ... RENAME COLUMN` / `RENAME TO` | ACCESS EXCLUSIVE (default rule) | everything | no |
| `ALTER TABLE ... DROP COLUMN` | ACCESS EXCLUSIVE | everything | no; space is not reclaimed |
| `ALTER TABLE ... ADD CONSTRAINT ... CHECK` | ACCESS EXCLUSIVE | everything | full scan unless `NOT VALID` |
| `ALTER TABLE ... ADD CONSTRAINT ... FOREIGN KEY` | SHARE ROW EXCLUSIVE on both tables | writes on both tables | full scan unless `NOT VALID` |
| `ALTER TABLE ... ADD CONSTRAINT ... UNIQUE/PRIMARY KEY USING INDEX` | ACCESS EXCLUSIVE | everything | no; reuses a prebuilt unique index |
| `ALTER TABLE ... VALIDATE CONSTRAINT` | SHARE UPDATE EXCLUSIVE | other DDL; not reads or writes | full scan |
| `ALTER TABLE ... SET STATISTICS` / `SET (storage params)` | SHARE UPDATE EXCLUSIVE | other DDL | no |
| `ALTER TABLE ... ATTACH PARTITION` | SHARE UPDATE EXCLUSIVE on parent, ACCESS EXCLUSIVE on the attached table and default partition | see left | scan of the attached table to check the partition bound |
| `ALTER TABLE ... DETACH PARTITION CONCURRENTLY` | SHARE UPDATE EXCLUSIVE | other DDL | no |
| `CREATE TRIGGER` | SHARE ROW EXCLUSIVE | writes | no |
| `DROP TABLE`, `TRUNCATE`, `VACUUM FULL`, `CLUSTER`, `REINDEX` (non-concurrent) | ACCESS EXCLUSIVE | everything | `VACUUM FULL`, `CLUSTER` rewrite |

## Type changes that do and do not rewrite

The rule from `ALTER TABLE` notes: no rewrite when the old type is binary coercible to the new one (or an unconstrained domain over it) and `USING` does not change the values.

- No rewrite: `varchar(n)` to `text`, `text` to `varchar` (no collation change), `varchar(n)` to `varchar(m)` with `m > n`, `varchar(n)` to unbounded `varchar`.
- Rewrite: `int` to `bigint`, `text` to `int`, any change with a `USING` expression that computes new values, shrinking `varchar(n)`.
- A collation change rebuilds the indexes on the column even without a rewrite.

For a rewriting change on a large table, use expand and contract instead: add a new column of the new type, dual-write, backfill in batches, switch reads, drop the old column.

## The lock queue

A request for ACCESS EXCLUSIVE that is waiting behind a long-running transaction blocks every later request on that table that conflicts with it, including plain `SELECT`, until it is granted or cancelled. So a "fast" `ALTER TABLE` that cannot get its lock immediately stalls all traffic to the table. `lock_timeout` bounds that stall.

To see who blocks whom during an incident:

```sql
SELECT pid, pg_blocking_pids(pid) AS blocked_by, wait_event_type, state,
       now() - xact_start AS xact_age, left(query, 80) AS query
FROM pg_stat_activity
WHERE cardinality(pg_blocking_pids(pid)) > 0;
```
