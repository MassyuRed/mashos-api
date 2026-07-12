# Gate A GA0-GA1 implementation result (2026-07-12)

## Scope

- Implemented: GA0 baseline freeze and GA1 structural RED.
- Production changes: none.
- API / DB / RN production changes: none.
- Historical FB172 ledger changes: none.
- GA2 and later phases: not started.

## GA0 baseline

The received archive was executed from an untouched extraction.  The existing
RR0 fingerprint algorithm was reused without changing its include/exclude
rules.

| Evidence | Frozen result |
|---|---|
| received archive | `mashos-api(214).zip` |
| archive SHA-256 | `9fbe8ed2ba6b0d245a60aa4f6f0c6a73cce5c58f77adfbaa4f6a5769ba72b9f7` |
| source fingerprint | `394b5da7a9546d5f893e00fe27417e2e10231dcc267a2d728e6f11025d2aa0c3` |
| source file count | `1359` |
| same16 case count | `16` |
| same16 body-free signature | `33b2431216abb243c0fcee43dbe8dfe6bf81546c1df6e37b453d04ce449e475b` |
| full collect | `12714 collected / 0 errors` |
| full backend | `12543 passed / 169 failed / 2 skipped` |
| failure node duplicates | `0` |
| failure set ID | `post_fb172_residual_fd8dc9bd19e9` |
| failure node refs SHA-256 | `fd8dc9bd19e95db6edcb8dce951dedc50a477865145c8f5c3d08c92e978fc34a` |
| historical FB172 ledger SHA-256 | `7a166e785c387c30cf89c6935da4c086cee6d870d8a121b4f6d7ffa796a3587c` |

The body-free freeze contains all 169 node refs.  Raw current input and reply
bodies were used only for the local read-only run and are not included in the
handoff artifact set.  The integrity test regenerates only in memory and
compares hashes, character counts, and line counts.

An initial nonbaseline dependency probe used FastAPI `0.139.0` and produced
`171 failed`.  Its two extra failures were both route-inventory checks caused
by the newer lazy `include_router` representation.  Re-running with the
official compatible dependency set (FastAPI `0.115.12`, Starlette `0.46.2`,
Pydantic `2.11.7`, HTTPX `0.28.1`) restored those two checks to green without a
source change and reproduced the required 169-node baseline.

## GA0 validation

```text
GA0 integrity: 6 passed
existing Gate 0 semantic / surface / decision controls: 96 passed
post-GA1 working-tree collect: 12742 collected / 0 errors
compileall: passed
```

The post-GA1 collect is a collection-integrity check only.  It is not the GA4
final collect and does not replace the frozen pre-GA1 `12714 / 0` baseline.

## GA1 structural RED

The new RED file contains no expected completed reply body and no case-specific
production branch.  It exercises the following invariant families:

1. semantic contribution ownership and follow contribution;
2. self-denial counterdirection de-duplication with help-seeking controls;
3. normalized relation-surface stem budget;
4. retained-intention closure role / modality / scope compatibility;
5. dependent-clause integrity;
6. short-state one-line regression control;
7. case-ID and case-order metamorphic controls;
8. an AST guard against exact completed-body assertions.

Pre-GA2 result:

```text
13 failed / 9 passed
```

The failures are intentional GA1 REDs:

- 4 failures: D / I6-D01 duplicate protective-counterdirection ownership and
  triple delivery;
- 1 failure: B repeated normalized surface stem without a distinct expressed
  role;
- 8 failures: B / C / long / comparison families lack explicit
  retained-intention closure role, modality, and selected-target scope.

Passing controls cover I6-D02 / I6-D03 help-seeking distinction, B clause
integrity, all three short-state cases, metamorphic independence, and the
no-exact-body guard.

## Stop state

GA0 and GA1 are complete.  The structural REDs remain red by design.  No
production repair was performed because that belongs to GA2.
