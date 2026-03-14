# Cocolon Public API Contract Policy

Policy version: `2026-03-12.phase6e`

## Core rules

1. RN is display-only.
2. Existing requests are additive-only.
3. Existing responses are additive-only.
4. Breaking changes require a new endpoint or version.
5. The server absorbs compatibility for older builds.
6. Every public API response carries policy metadata headers.
7. Compatibility must be guarded by automated tests.
8. Deprecated public routes must declare their replacement route/version when one exists.

## Why this policy exists

This policy fixes the boundary that protects already-released mobile builds from backend evolution.
The goal is not merely "route everything through an API"; the goal is to keep the request/response
contract stable while allowing internal tables, workers, and publishing logic to evolve behind that boundary.

Phase 6-E keeps the route surface unchanged and extends state-backed governance to the
`/global_summary` public aggregate surface. The v1 contract stays fixed, while reads now prefer
READY daily summary artifacts and retain a legacy table / refresh fallback during migration.

## Runtime headers

Public responses carry these headers:

- `X-Cocolon-Request-Id`
- `X-Cocolon-Api-Policy-Version`
- `X-Cocolon-Contract-Id`
- `X-Cocolon-Deprecated`
- `X-Cocolon-Replacement` (when applicable)

## Client compatibility rules

- New required request fields must not be added to existing public routes.
- Existing response keys must not be renamed, removed, or type-changed.
- Older payloads must be normalized server-side with defaults, aliases, and enum coercion when feasible.
- Any truly breaking evolution must move to a fresh route (for example `/v2/...`).

## Enforcement

- `services/ai_inference/api_contract_registry.py` is the source of truth for v1 public routes.
- `services/ai_inference/middleware_api_contract.py` attaches runtime metadata headers.
- `scripts/check_no_direct_supabase.py` blocks RN direct Supabase regressions.
- `tests/contract/` verifies registry integrity, runtime headers, compatibility fixtures, and required route coverage.
