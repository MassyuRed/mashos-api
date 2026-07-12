# Gate 0 RR7–RR10 implementation result (2026-07-11)

## Source

- received archive: `mashos-api_3(117).zip`
- archive SHA-256: `805505a8afb1675206eb53a9b8d53225ee7cf463d7969f985ee829a605bff99e`
- post-RR7 source snapshot fingerprint: `88286e4499bcfa09d23d8db613f775a0890e2781cd22a2a7653badddaa50c340`
- snapshot file count: `1353`

## RR7: obsolete test import migration

The two deleted reply-service private helpers were not restored. Their historical tests now assert the current canonical Grounded Plan / Sentence Surface / Grounded Gate / Reply owners.

- old two-file collect: `13 tests collected / 0 errors`
- old two-file execution: `13 passed`
- I0 plus migrated tests: `20 passed`
- legacy substantive production reachability: `0`
- `emlis_ai_reply_service.__all__`: `render_emlis_ai_reply` only

## RR8: validation V1 → V5

Validation order was preserved. The source fingerprint matched at every step boundary.

| Step | Result |
|---|---|
| V1 compile / targeted | `186 passed, 41 subtests passed` |
| V2 safety / public contract | `77 passed` |
| V3 RN screen contract | `36 passed` |
| V4 full collect | `12,700 collected / 0 errors` |
| V5 full backend | `12,526 passed / 172 failed / 2 skipped / 41 subtests passed` |

The body-free evidence is `ai/tests/fixtures/gate0_rr8_validation_20260711.json`. It records all 172 failed node IDs without response bodies or raw input.

## Stop decision

V5 did not satisfy the design requirement `return code 0 / failed 0 / errors 0`. Therefore the cycle stopped with:

```text
GATE0_TEST_OR_CONTRACT_BLOCKED_STOPPED
```

No failing test was skipped, xfailed, removed, or rewritten merely to obtain green.

## RR9 / RR10 boundary

- same-16 regeneration / Karen actual read: not started because RR8 did not complete green
- new review receipt: not generated
- Gate 0 local-pass decision: not generated
- exact-8 device packet: not generated
- P5 formal 24: not started
- P6: not started
- P8: not started

This is the required fail-closed outcome. Continuing to RR9 or emitting exact 8 would contradict Sections 11–13 and RR8–RR10 of the design.
