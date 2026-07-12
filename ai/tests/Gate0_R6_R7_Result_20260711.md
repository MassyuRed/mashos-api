# Gate 0 R6 / R7 implementation result

## Scope

- Implemented: R6 I0 ledger and historical local-display test alignment to the final canonical cutover.
- Implemented: R7 targeted-to-affected validation matrix and failure classification.
- Not implemented: R8 local human read, R9 Gate 0 decision, device packet, or later work.
- Production source changes in R6/R7: none.
- API / DB / RN public contract changes: none.

## Received basis

- archive: `mashos-api_4(112).zip`
- archive SHA-256: `1049e10b29726ffc7098a59aad2d6c008d743788b0369f1ef4131b73ff06f305`
- R4/R5 production fingerprints matched the previously validated implementation.
- R6 received RED: three I0 final-cutover drift failures and one historical-meta drift failure.

## R6 final-cutover alignment

The I0 inventory now freezes every listed final source fingerprint; the former
intentional-modification skip set is empty.  It also includes the canonical
plan, sentence/surface, and semantic Gate modules.

The actual import graph is recorded as:

```text
emlis_ai_reply_service
  -> emlis_ai_grounded_observation_plan
  -> emlis_ai_grounded_sentence_surface
  -> emlis_ai_grounded_observation_gate
```

All three canonical modules are production-reachable.  The former completed
surface, recomposition, limited-grounding, low-information question, fixed
self-denial, material-bundle, and limited-composer owners are recorded as
non-public shadow modules.  Their known fixture phrases have zero occurrence
in the production-reachable graph.  Emergency and support-required Safety
ownership remains production-reachable.

The historical Phase20-10 test now reads the current body-free
`grounded_observation` metadata.  It checks canonical generation path,
`grounded_plan_realizer`, semantic Gate pass, public connection, and
`product_readfeel_status=not_evaluated`.  It no longer requires removed
material slots, unknown slots, or recovery attempts.  Its receipt explicitly
states `historical_local_display_only` and `actual_device_evidence=false`.

R6 validation:

- I0 final-cutover inventory plus historical Phase20-10: 11 passed.
- R0 immutable case/source baseline: 3 passed.
- False failures after alignment: 0.
- Body-defect masking expectation changes: 0.

## R7 affected validation matrix

| Group | Result | Scope |
| --- | ---: | --- |
| Grounded R1/R5 and I1-I7 targeted | 118 passed, 41 subtests passed | retention, relation, lexical, follow, Gate, recovery, local candidate guard |
| Safety / response / public feedback affected | 91 passed, 1 deselected | Safety owner, response contract, public status, RN eligibility, body-free metadata |
| I0 / historical display | 11 passed | fingerprint, owner graph, legacy reachability, current canonical meta |
| Anti-template / metamorphic | 55 passed, 25 subtests passed | repetition guard, template guard, paraphrase and structural perturbation |
| Compile | passed | all three modified R6 files |
| Full collect-only | 12,626 collected, 2 classified pre-existing errors | no full-suite-green claim |

The one deselected affected test imports the removed private helper
`_build_runtime_surface_pre_return_report_for_candidate`.  The same failure
reproduces on the unmodified received archive, so it is classified as
pre-existing and unrelated to R6/R7.

Full collect-only reproduces two received-snapshot collection errors:

- missing `_regeneration_reasons_for_retry`
- missing `_reply_service_recomposition_existing_gate_chain_summary`

Both were already frozen before R6/R7 and reproduce without these changes.
They block a full-backend-green claim but do not create an unclassified R6/R7
failure.

## Boundary

- Modified and adjacent R6/R7 suites: green.
- Unclassified failures: 0.
- Full backend suite green: not claimed.
- Product Read Feel / human pass: not evaluated.
- Device evidence: not produced.
- Gate 0 pass, P5/P6/P8 entry, release readiness: not claimed.
- Next authorized boundary: R8 only; it was not started here.
