# Gate 0 R0 / R1 implementation result

## Scope

- Implemented: R0 baseline / owner / defect freeze.
- Implemented: R1 failing structural tests first.
- Not implemented: R2 or later production repair.
- Production source changes: none.

## R0 freeze

Received source snapshot:

- archive: `mashos-api(204).zip`
- archive SHA-256: `8cdcd9036db92596bd1a1ce47141f3c1af809e957ebe5e6352684413e94d8015`
- case source of truth: existing Known A-D helper plus existing I6 unseen 12 helper
- case count: 16
- subscription tier: `free`
- history / context mock: none

The body-full baseline is kept only at
`ai/tests/local_only/emlis_gate0_r0_baseline_20260711.json`. It contains the
unchanged normalized input, current comment, body-free Grounded meta, and
body-free plan / relation / sentence debug for every case. It must not be
copied into public metadata or runtime responses.

The body-free freeze manifest at
`ai/tests/fixtures/emlis_gate0_r0_freeze_20260711.json` records canonical source
fingerprints, the actual runtime owner graph, selected-suite results, and all
failure classifications.

## Owner result

The received snapshot has already cut over to the canonical path:

```text
emlis_ai_reply_service
  -> emlis_ai_grounded_observation_plan
  -> emlis_ai_grounded_sentence_surface
  -> emlis_ai_grounded_observation_gate
```

All three Grounded modules are production-reachable from
`emlis_ai_reply_service`. The older I0 inventory still marks part of this graph
as shadow, so its old owner expectations are historical drift, not evidence
that the current path is unreachable.

## Pre-R1 failure classification

Selected Grounded I1-I7 plus I0 inventory:

- 73 passed
- 3 failed
- 41 subtests passed

The three failures are fully classified:

1. `snapshot_fingerprint_mismatch`
2. `runtime_ownership_mismatch`
3. `legacy_phrase_reachability_mismatch`

Unclassified failures: 0.

Historical Phase20-10 local display suite:

- 3 passed
- 1 failed

The one failure is `historical_meta_contract_mismatch`: the historical test
expects the removed top-level `material_quality=low_information` contract,
while the current result exposes no value at that old lookup. This test is
local historical evidence, not actual-device provenance.

## R1 intentional RED

`ai/tests/test_emlis_ai_gate0_r1_semantic_retention.py` adds only structural
expectations. It does not assert an exact completed public body.

Current R1 result:

- 0 passed
- 11 failed

The RED set covers:

- Known B whole-input required nuclei
- I6-L01 required nuclei beyond the old four-item cap
- I6-L02 relation endpoints and direction
- I6-L03 required nuclei, reversal direction, and false shift rejection
- I6-S03 lexical fidelity and duplicate-anchor integration
- Known D / I6-D01 protective counterdirection follow role

The failures reproduce the approved defects without adding a fixture branch to
production. They are expected to turn green only through R2-R5 repairs.

## Stop / next boundary

R0 stop conditions were not met: the case source matches the received helpers,
and the snapshot fingerprints were frozen from the received archive.

This result does not claim Gate 0 pass, Product Read Feel pass, device pass, P5
entry, P6 entry, P7 completion, P8 entry, or release readiness. The next
authorized implementation boundary is R2; it was not started here.
