# Cocolon Structure Unification Addendum — 2026-04-21

This addendum records the runtime contracts that were missing from the earlier
"名称混在 / 構造混在" design memo and are now reflected in code.

## 1. Piece public-read contract

- `api_emotion_reflection.py` remains the write-side entry for preview / publish / cancel / quota.
- `emotion_reflection_store.py` remains the live `emotion_generated` source owner.
- `api_nexus.py` is the public read-side surface for:
  - reflections list
  - reflection detail
  - reflection unread status façade
  - Nexus aggregation endpoints
- `api_mymodel_qna.py` remains the compatibility / reaction layer and is no longer a required direct caller for Nexus public reads.

## 2. Analysis artifact contract

- `/myweb/reports/ready` now treats projection-first artifact loading as the primary path.
- legacy ready fallback is behind `MYWEB_READY_ALLOW_LEGACY_FALLBACK` and defaults to disabled.
- `/myweb/reports/{report_id}/weekly-days` now treats saved artifact data as canonical.
- computed read-side reconstruction is behind `MYWEB_WEEKLY_DAYS_ALLOW_COMPUTED_FALLBACK` and defaults to disabled.

## 3. Self Structure latest ownership

- `api_myprofile.py` keeps stale-detection, access gating, and response shaping.
- `astor_myprofile_report.refresh_myprofile_latest_report()` becomes the shared latest-report refresher used by both worker/runtime and route-triggered refresh.
- latest generation parameters are explicit:
  - `period_override`
  - `report_mode_override`
  - `trigger`

## 4. EmlisAI reader boundary

- `emlis_ai_context_service.py` no longer imports route helpers directly.
- `emlis_ai_readers.py` is the adapter boundary for read-side payload builders used by EmlisAI.
- This is an intermediate contract: route-coupled payload builders are centralized behind one reader layer so that lower-level extraction can happen without reopening EmlisAI itself.
