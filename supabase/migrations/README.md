# Piece M0/M1 tracked migration candidate

Application identity: `mashos-api.supabase.migrations.v1`.

**Not applied. Not B2-A GREEN. Not deployable until the six caller rebindings and
the unchanged native PostgreSQL/psycopg test are verified.**

## Scope and immutable history

`APPLIED_MIGRATIONS_ARE_IMMUTABLE`.
`PRODUCTION_APPLICATION_REQUIRES_SEPARATE_MASH_APPROVAL`.
`ROLLBACK_AND_POSTVERIFICATION_REQUIRED`.

The Piece manifest is a Piece-only ledger, not an inventory claiming that the
whole migrations directory was empty. The two existing September Emlis SQL
files remain separate and unchanged. No migration is automatically applied.

`PCE0_CATALOG_SHA256`: `2f51e5e6e4207a186aaacbeb355c07ade3b4f777960f3f46d1dbea9f8f9d810e`.
This identifies the historical 2026-08-07 PCE-0 packet. Its absent application
migration relation is historical, not a claim about today's connected database.
No current/live catalog was queried by this candidate. Before any later live
DDL, obtain the authorized current catalog, compare/reconcile drift against
PCE-0, and verify the repository ledger and SQL hashes. Do not invent a matching
current checksum or mark an unapplied migration as applied.

## M1 contract

The single-statement SQL first verifies the consumed 21-column names/types,
legacy relation kinds, invoker view definition and allowed read grant shape.
Unexpected column-level grants on either view are rejected before any change.
It creates only `public.mymodel_reflections_read`, preserving the underlying
rows and `public.pieces`. Default/previous bridge grants are removed; only
legacy service-role SELECT access is copied. Source-table RLS is not changed.
This narrow SQL preflight is not a checksum proof of the complete PCE-0 packet.

A drift exception aborts the whole statement. Re-execution only accepts an
already equivalent bridge; incompatible pre-existing objects are rejected.
No SQL creates Piece V2 records, preview IDs, quota, lifecycle functions, or
changes old Q&A/public Piece semantics.

## Disposable PostgreSQL verification

Install only `requirements-piece-v2-test.txt` into a disposable test environment.
Provision an empty, local PostgreSQL 15+ database named `piece_v2_test_b2a`.
Use only synthetic data; the frozen test drops/recreates its own fixture tables
inside rollback-only transactions. Never point it at a database with real data.

```sh
export PIECE_V2_TEST_DATABASE_URL='postgresql://test_user@127.0.0.1:5432/piece_v2_test_b2a'
export PIECE_V2_TEST_DATABASE_DISPOSABLE_ACK='I_ACKNOWLEDGE_DISPOSABLE_DATABASE'
python -m pytest -q ai/tests/piece_v2/db/test_b02_m0_m1_legacy_bridge.py
```

The database must be provisioned explicitly by its owner. The conftest accepts
only numeric loopback or an explicit Unix socket directory and the test DB
prefix; libpq host/database override query parameters are rejected. It does
not connect, install a driver, create a DB, or replace missing evidence with a
skip. Missing URL/driver remains NONCREDIT. PGlite/SQL-only diagnostics are
supplementary and cannot establish the frozen psycopg acceptance result.

## Reader transition and rollback

The exact six preimages are in the manifest. The intended narrow change removes
`COCOLON_PIECES_READ_TABLE` from their read selector, retains both existing
MYMODEL_REFLECTIONS_READ_TABLE overrides, and defaults to
`mymodel_reflections_read`. Write table names, queries, filters, auth checks and
response shapes do not change. Re-scan the current repository before rebinding;
any seventh caller requires scope reconciliation, not a silent omission.

For any later separately authorized application, apply/verify the bridge before
deploying rebinding code. A rollback restores these six read selectors first;
only then may an explicitly authorized transaction remove an otherwise unused
bridge. Never replace/drop `public.pieces` or mutate shared source rows here.
Check source row identities/counts, view definition/ACL, owner-only/service-role
access and all six query paths before declaring success. B2-B and later work
are separate; `automatic_progression=false`.
