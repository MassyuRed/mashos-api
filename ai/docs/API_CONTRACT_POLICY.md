# Cocolon Public API Contract Policy

Policy version: `2026-03-20.mymodel-qna-unread-status.v1`

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

This policy revision adds `/mymodel/qna/unread-status` so MyModel Home unread
aggregation stays server-owned across the viewer's accessible reflections, while existing
v1 routes remain additive-only and backward compatible.

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
- Nested additive metadata is allowed when existing primary fields remain stable (for example `input_feedback.comment_text` stays stable while `input_feedback.emlis_ai` is additive-only).
- EmlisAI observation-kernel metadata may expand inside `input_feedback.emlis_ai` (for example `used_memory_layers`, `reply_length_mode`, `evidence_by_line`, `model_revision`) without changing the stable `comment_text` contract.
- Subscription bootstrap plan metadata may expand inside `plans.*.emlis_ai` with server-owned capability hints (for example `model_mode`, `interpretation_mode`, `reply_length_mode`) while existing keys remain backward compatible.
- Older payloads must be normalized server-side with defaults, aliases, and enum coercion when feasible.
- Any truly breaking evolution must move to a fresh route (for example `/v2/...`).

## Enforcement

- `services/ai_inference/api_contract_registry.py` is the source of truth for v1 public routes.
- `services/ai_inference/middleware_api_contract.py` attaches runtime metadata headers.
- `scripts/check_no_direct_supabase.py` blocks RN direct Supabase regressions.
- `tests/contract/` verifies registry integrity, runtime headers, compatibility fixtures, and required route coverage.
