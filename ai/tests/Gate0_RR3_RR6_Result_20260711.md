# Gate 0 RR3 / RR4 / RR5 / RR6 implementation result

## Scope

- Implemented: RR3 SentencePlan line structure repair.
- Implemented: RR4 relation grammar repair.
- Implemented: RR5 human-follow and dependent-clause surface repair.
- Implemented: RR6 Gate 0 decision contract v2.
- Not implemented: RR7 or later test-import migration, final fingerprint refresh, validation execution, or same-16 human review.
- API, DB, RN, Safety owner, and public response-key changes: none.

## RR3 SentencePlan line structure

- `expected_human_follow_role()` now reuses the Plan-owned classifier.
- role / target incompatibility fails structurally instead of falling back.
- follow delivery is recorded as `integrated` or `separate` in body-free atoms.
- adjacent source-local state nuclei can be grouped without dropping nucleus or evidence ids.
- duplicate anchor delivery without a new relation, boundary, Safety, or distinct follow responsibility is rejected.
- relation lines carry semantic surface-role and endpoint-form atoms.

Known A is one observation delivery unit in every recovery stage.  Short-state
and self-denial controls retain their prior delivery responsibilities.

## RR4 relation grammar

Relation type and surface role are now separated.  The renderer uses endpoint
semantic roles and endpoint clause forms for:

- burden or constraint with progress
- provisional evaluation to counterevidence
- comparison to counterevidence
- coexisting comparison and evidence
- intention evidenced by action
- bounded fallback contrast

I6-L03 preserves the source predicate once; the former generic predicate is
not appended to an already complete endpoint clause.  Relation ids, endpoint
ids, and direction are unchanged.

## RR5 human follow and clause surface

- retained intention is no longer surfaced as a completed change.
- integrated follow does not create a second anchor line.
- B uses an internal-only `SurfaceClauseUnit` to preserve interrogative /
  quotative dependency and complete-clause structure.
- no persistent Plan or public schema field was added.
- no case id, fixture phrase, or completed-body bank was added to production.

The existing Plan tie-breaker was also tightened so explicit role evidence is
preferred over kind-only classification.  This keeps I6-L01 on the explicit
next intention rather than the earlier completed action.

## RR6 Gate 0 decision contract v2

`Gate0ValidationEvidence` now requires explicit source snapshot, targeted,
safety/public, RN, full collect, collection-error, full backend, and
unclassified-failure evidence.

- old `affected_suites_green` / `unclassified_failure_count` inputs removed
- validation evidence and expected snapshot are mandatory
- full-collect boolean is checked against return code, collected count, and error refs
- review / validation / expected source fingerprints must match
- validation-blocked review pass returns `GATE0_TEST_OR_CONTRACT_BLOCKED_STOPPED`
- repair review remains `GATE0_REPAIR_RETURN_STOPPED` while retaining validation blockers
- exact-8 builder rechecks the full v2 validation and snapshot contract
- artifact generator no longer contains hard-coded green inputs

No new validation receipt or v2 decision was fabricated in RR6.  The generator
requires an explicit validation-evidence file and refuses stale review/source
fingerprints.

## Validation

- RR0/RR1/RR3-RR6 and Grounded affected set: 179 passed, 41 subtests passed
- selected Safety/public response contract: 46 passed
- modified/new Python compile: passed
- full collect-only: 12,687 collected, 2 errors

The two collect errors are the frozen RR0 blockers:

- `_regeneration_reasons_for_retry`
- `_reply_service_recomposition_existing_gate_chain_summary`

They reproduce on the received archive and remain assigned to RR7.  Production
private helpers were not restored.

Three additional historical reply-service test files produced 13 stale
private-owner failures both before and after this change.  They are not counted
as new RR3-RR6 regressions and were not made green by restoring removed routes.

## Boundary

This result does not claim full collect success, full backend green, Gate 0
pass, same-16 human pass, device pass, P5/P6/P8 entry, or release readiness.
The next authorized implementation boundary is RR7.
