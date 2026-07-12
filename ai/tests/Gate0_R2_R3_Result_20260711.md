# Gate 0 R2 / R3 implementation result

## Scope

- Implemented: R2 required nucleus / whole-input retention repair.
- Implemented: R3 relation type / endpoint / direction / reversal repair.
- Not implemented: R4 or later lexical fidelity, human-follow role, Gate, or final read-feel repair.
- API / DB / RN public contract changes: none.

## Received basis

- archive: `mashos-api_2(140).zip`
- archive SHA-256: `5b8ca5f412f2d621643ae3b9887caca8d1bb737007ce05ff4a4f54fb61ab8045`
- R0 baseline integrity before implementation: 3 passed
- R1 received RED before implementation: 11 failed

## R2

`emlis_ai_grounded_observation_plan.py` now assigns body-free semantic arc
roles to existing Evidence spans. The roles cover initial condition, local
turn endpoints, embedded turns, current change, explicit result/evaluation,
provisional evaluation, counterevidence, limiting unknown, retained intention,
and concrete action evidence.

Required retention is now based on those major-turn obligations. The former
four-required-span cap and first/last-field ownership are removed. A separate
`memo_action` contributes its strongest concrete action evidence once and no
longer replaces the memo's central arc.

Response primary selection now scores semantic roles and required relation
endpoints. It no longer takes the first three required nuclei solely by
priority. Recovery groups required relation components together so every
stage keeps the same required nucleus/relation set without increasing line
count at `optional_removed`.

## R3

Relation markers now use the nearest substantive nuclei in the same source
field. A marker whose two sides remain inside one Evidence span keeps that
span as an embedded major turn and does not invent a cross-span edge.

`shift_from_to` now requires an explicit prior/current dimension or a real
time-direction pair. A generic shift-like token in either endpoint is no
longer enough. L03 therefore keeps the pale result to provisional failure as
bounded context and promotes provisional failure to discovered pattern as the
required `preserves_despite` reversal.

Relation candidates are resolved by grounding strength, source provenance,
semantic specificity, and certainty. Cross-field `action_supports_change`
becomes required only when a required intention/change is linked to the
selected concrete action evidence. Syntactically dependent ledger fragments
remain required when they own a major turn, but they are recombined for
surface binding instead of becoming false from/to endpoints.

The I6 metamorphic fixtures were corrected so they test a genuine inter-span
cause boundary (`そのため`) and a genuine cross-span contrast. They no longer
require an internal cause marker to be attached to an unrelated following
span. The I1 Known B test likewise verifies that an embedded marker does not
create a fabricated cross-span relation.

## Validation

R2 / R3 structural RED subset:

- 7 passed
- 4 R4 tests deselected

Relation metamorphic subset:

- 4 passed
- 9 subtests passed

R0 baseline:

- 3 passed

Grounded I1-I6 plus response / Safety adjacent suite:

- 99 passed
- 25 subtests passed
- 1 unrelated Pydantic deprecation warning
- 4 expected R4 RED failures remain

The remaining four R1 failures are exactly:

1. S03 lexical predicate policy
2. S03 integrated short follow
3. Known D protective counterdirection follow role
4. I6-D01 protective counterdirection follow role

I7 stays blocked before R4/R5. Known B and Known C still exceed the current
surface-length limit, so the old automated candidate cannot open P5 entry.
This is not changed to green by expectation updates.

Full backend collect-only reached 12,597 collected tests and reproduced two
pre-existing collection errors. The same two errors reproduce on the received
snapshot and are unrelated to R2/R3:

- missing `_regeneration_reasons_for_retry`
- missing `_reply_service_recomposition_existing_gate_chain_summary`

## Boundary

This result does not claim Gate 0 pass, local human read pass, device pass, P5
entry, P6 entry, P7 completion, P8 entry, or release readiness. The next
authorized implementation boundary is R4; it was not started here.
