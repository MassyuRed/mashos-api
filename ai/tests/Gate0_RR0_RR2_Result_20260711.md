# Gate 0 RR0 / RR1 / RR2 implementation result

## Scope

- Implemented: RR0 current freeze.
- Implemented: RR1 structural REDs.
- Implemented: RR2 Plan-side human-follow role / target repair.
- Not implemented: RR3 or later SentencePlan, relation grammar, compaction, or Gate decision repair.
- API, DB, RN, Safety owner, and public response contract changes: none.

## RR0 current freeze

- received archive: `mashos-api(207).zip`
- received archive SHA-256: `cfb378d93a7ff9d65542012ca3176cea6fb5f20f1a49756df16971eb37e93b00`
- deterministic source-tree fingerprint: `8d80af59708affcc0b4ee66c694330e71a08cb7de8b9bc359ff70ffbf7ad2cfe`
- fingerprinted source/config files: 1,348
- frozen cases: 16
- local human pass / repair required / hard fatal: 7 / 9 / 0
- frozen collection blockers: 2

The body-free freeze is stored at
`ai/tests/fixtures/gate0_rr0_freeze_20260711.json`.  The exact current inputs
and bodies are stored only at
`ai/tests/local_only/gate0_rr0_body_local_20260711.json`.

The existing R8 receipt and R9 decision were not overwritten.  Regenerated
current body hashes and normalized input hashes matched the existing R8 local
comparison for all 16 cases.

## RR1 structural RED

The new structural file contains no exact completed-body assertion.  On the
unmodified received source, its result was:

- 1 passed
- 28 failed

The failures cover:

- shared intention-role classification
- human-follow target selection
- self-denial / help-seeking priority controls
- relation surface roles
- duplicate anchor and repeated observation delivery
- dependent-clause unit planning
- explicit Gate 0 validation evidence input

## RR2 Plan repair

`emlis_ai_grounded_observation_plan.py` now owns a body-free shared classifier
and role-first target selection.  Normal safe observation and self-denial use
different role priorities.  The selection uses existing nucleus attributes,
retention, response membership, relation connection, grounding, and source
order; it does not inspect case ids or fixture text.

The persistent Plan schema is unchanged.  The semantic version changed from
`cocolon.emlis.grounded_semantics.i2.v1` to
`cocolon.emlis.grounded_semantics.i2.v2`.

RR2-owned structural results:

- intention / target / control / self-denial subset: 20 passed
- RR0 integrity: 4 passed
- existing Grounded R1/R5/R8 and I1-I7 affected set: 123 passed, 41 subtests passed
- Python compile for all modified/new Python files: passed

After RR2, the full RR1 file is 21 passed and 8 intentionally RED.  The eight
remaining REDs are owned by later authorized steps:

- RR3/RR4 relation surface-role atoms: 5
- RR3/RR5 duplicate delivery / dependent-clause units: 2
- RR6 Gate 0 validation evidence contract: 1

These failures were not weakened, xfailed, or converted into exact-body
expectations.

## Boundary

This result does not claim the nine read-feel defects are repaired, Gate 0
pass, Product Read Feel pass, device pass, P5/P6/P8 entry, full collect success,
or full backend green.  The next authorized implementation boundary is RR3.
