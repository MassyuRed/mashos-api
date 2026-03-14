# National Alignment Audit — Phase 5

## Alignment target

This phase translates the national architecture direction into enforceable runtime policy:

- RN remains display-oriented.
- Public behavior is governed at the API boundary.
- Compatibility for older builds is preserved at the server boundary.
- Observability and policy metadata are emitted on every public response.

## What Phase 5 adds

1. A public API contract registry for v1 mobile-facing routes.
2. Runtime response headers for policy version, request ID, contract ID, and deprecation metadata.
3. Automated compatibility tests for legacy `/emotion/submit` behavior.
4. Guardrails against RN direct Supabase regressions.
5. Documentation that makes the contract policy auditable.

## What is aligned now

- RN direct table reads/writes are guarded against regression.
- Public contract ownership is explicit and centralized.
- Compatibility policy is testable instead of implicit.
- The backend can evolve internal tables and logic without forcing a mobile rebuild, as long as the public contract stays additive.

## Remaining gaps after Phase 5

- CI wiring still needs to run the guard script and contract tests automatically.
- Remaining raw `fetch()` usage in RN should be consolidated through `lib/apiClient.js`.
- Publish governance is not yet fully standardized behind a shared helper such as `decide_publish()`.
- Older legacy surfaces still need to converge further on a single publish-governed boundary.

## Operational meaning

Phase 5 does not finish the architecture journey; it changes the failure mode.
Instead of relying on memory and manual discipline, the repo now has a registry, runtime metadata,
and tests that can reject accidental contract drift before release.