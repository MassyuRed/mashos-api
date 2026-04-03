# -*- coding: utf-8 -*-
"""generated_reflection_maintenance.py

Backfill / cleanup helpers for Premium generated reflections.

Goals
-----
- persist generated display bundles for existing rows
- remove inactive archived clones that are exact duplicates of a kept row
- optionally archive active duplicates when the question + normalized display are identical
- report unresolved "same question, multiple different answers" groups so the next
  stable-topic work can target them explicitly

This module intentionally stays deterministic and admin-task oriented.
It does not change the public API contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from astor_reflection_store import (
    REFLECTIONS_TABLE,
    _row_id,
    _row_locked,
    _row_public_id,
    _sb_delete,
    _sb_get_json,
    _sb_patch_json,
)
from generated_reflection_display import (
    GENERATED_REFLECTION_DISPLAY_VERSION,
    _extract_display_bundle,
    _stored_generated_display_result_from_row,
    apply_generated_display_to_content_json,
    build_generated_reflection_display,
    compute_generated_display_source_signature,
    resolve_generated_reflection_display,
)

_REQUIRED_DISPLAY_KEYS: Tuple[str, ...] = (
    "answer_display_state",
    "answer_format_version",
    "answer_format_meta",
    "answer_display_updated_at",
    "rewritten_answer_text",
    "answer_norm_hash",
    "display_source_signature",
)


@dataclass(frozen=True)
class GeneratedBackfillPlan:
    reflection_id: str
    content_json: Dict[str, Any]
    reason: str
    answer_norm_hash: str


@dataclass(frozen=True)
class GeneratedCleanupAction:
    action: str  # keep | delete | archive | protected
    reflection_id: str
    reason: str
    owner_user_id: str
    question: str
    answer_norm_hash: str
    is_active: bool
    public_id: str


def _now_iso_z_precise() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")



def _parse_mapping(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return dict(parsed)
        except Exception:
            return {}
    return {}



def _collect_text_candidates_from_row(row: Mapping[str, Any]) -> List[str]:
    content_json = _parse_mapping((row or {}).get("content_json"))
    source_refs = content_json.get("source_refs")
    out: List[str] = []
    if isinstance(source_refs, list):
        for ref in source_refs:
            if isinstance(ref, dict):
                for key in ("text_primary", "text_secondary", "question_text"):
                    value = str(ref.get(key) or "").strip()
                    if value and value not in out:
                        out.append(value)
    return out



def _compute_row_display_signature(row: Mapping[str, Any]) -> str:
    content_json = _parse_mapping((row or {}).get("content_json"))
    return compute_generated_display_source_signature(
        question=(row or {}).get("question"),
        raw_answer=(row or {}).get("answer"),
        category=(row or {}).get("category"),
        focus_key=content_json.get("focus_key") or (row or {}).get("focus_key"),
        topic_summary_text=content_json.get("topic_summary_text") or (row or {}).get("topic_summary_text"),
        text_candidates=_collect_text_candidates_from_row(row),
    )



def _build_fresh_display_result(row: Mapping[str, Any]):
    content_json = _parse_mapping((row or {}).get("content_json"))
    return build_generated_reflection_display(
        question=(row or {}).get("question"),
        raw_answer=(row or {}).get("answer"),
        category=(row or {}).get("category"),
        focus_key=content_json.get("focus_key") or (row or {}).get("focus_key"),
        topic_summary_text=content_json.get("topic_summary_text") or (row or {}).get("topic_summary_text"),
        text_candidates=_collect_text_candidates_from_row(row),
    )



def _display_bundle_complete(row: Mapping[str, Any]) -> bool:
    bundle = _extract_display_bundle(row)
    state = str(bundle.get("answer_display_state") or "").strip().lower()
    if state not in {"ready", "masked", "blocked"}:
        return False
    for key in _REQUIRED_DISPLAY_KEYS:
        if key not in bundle or bundle.get(key) in (None, ""):
            return False
    if state != "blocked" and not str(bundle.get("answer_display_text") or "").strip():
        return False
    return True



def build_generated_reflection_backfill_plan(row: Mapping[str, Any]) -> Optional[GeneratedBackfillPlan]:
    reflection_id = _row_id(dict(row or {}))
    if not reflection_id:
        return None

    bundle = _extract_display_bundle(row)
    current_signature = _compute_row_display_signature(row)
    stored_signature = str(bundle.get("display_source_signature") or "").strip()
    stored_version = str(bundle.get("answer_format_version") or "").strip()
    stored_result = _stored_generated_display_result_from_row(row)

    reasons: List[str] = []
    if stored_result is None:
        reasons.append("missing_or_stale_display")
    if not _display_bundle_complete(row):
        reasons.append("incomplete_display_bundle")
    if stored_signature != current_signature:
        reasons.append("display_source_signature_mismatch")
    if stored_version != GENERATED_REFLECTION_DISPLAY_VERSION:
        reasons.append("display_version_refresh")

    if not reasons:
        return None

    result = _build_fresh_display_result(row)
    updated_content_json = apply_generated_display_to_content_json(
        _parse_mapping((row or {}).get("content_json")),
        result=result,
        display_updated_at=_now_iso_z_precise(),
    )
    if updated_content_json == _parse_mapping((row or {}).get("content_json")):
        return None

    return GeneratedBackfillPlan(
        reflection_id=reflection_id,
        content_json=updated_content_json,
        reason=",".join(sorted(set(reasons))),
        answer_norm_hash=str(result.answer_norm_hash or "").strip(),
    )



def _status_rank(row: Mapping[str, Any]) -> int:
    status = str((row or {}).get("status") or "").strip().lower()
    is_active = bool((row or {}).get("is_active"))
    if is_active and status in {"ready", "published"}:
        return 5
    if is_active:
        return 4
    if status in {"ready", "published"}:
        return 3
    if status == "draft":
        return 2
    if status in {"archived", "rejected", "failed"}:
        return 1
    return 0



def _sort_desc_key(row: Mapping[str, Any]) -> Tuple[int, str, str]:
    updated_at = str((row or {}).get("updated_at") or (row or {}).get("created_at") or "")
    return (_status_rank(row), updated_at, _row_id(dict(row or {})))



def plan_generated_reflection_duplicate_cleanup(
    rows: Sequence[Mapping[str, Any]],
    *,
    archive_active_duplicates: bool = True,
) -> List[GeneratedCleanupAction]:
    grouped: Dict[Tuple[str, str, str], List[Mapping[str, Any]]] = {}
    for row in rows or []:
        if str((row or {}).get("source_type") or "").strip() != "generated":
            continue
        question = str((row or {}).get("question") or "").strip()
        if not question:
            continue
        display_result = resolve_generated_reflection_display(row)
        answer_norm_hash = str(getattr(display_result, "answer_norm_hash", "") or "").strip()
        if not answer_norm_hash:
            continue
        key = (
            str((row or {}).get("owner_user_id") or "").strip(),
            question,
            answer_norm_hash,
        )
        grouped.setdefault(key, []).append(dict(row or {}))

    actions: List[GeneratedCleanupAction] = []
    for (owner_user_id, question, answer_norm_hash), group_rows in grouped.items():
        if len(group_rows) <= 1:
            only = group_rows[0]
            actions.append(
                GeneratedCleanupAction(
                    action="keep",
                    reflection_id=_row_id(only),
                    reason="unique_group",
                    owner_user_id=owner_user_id,
                    question=question,
                    answer_norm_hash=answer_norm_hash,
                    is_active=bool(only.get("is_active")),
                    public_id=_row_public_id(only),
                )
            )
            continue

        ordered = sorted(group_rows, key=_sort_desc_key, reverse=True)
        keeper = ordered[0]
        keeper_id = _row_id(keeper)
        actions.append(
            GeneratedCleanupAction(
                action="keep",
                reflection_id=keeper_id,
                reason="duplicate_group_keeper",
                owner_user_id=owner_user_id,
                question=question,
                answer_norm_hash=answer_norm_hash,
                is_active=bool(keeper.get("is_active")),
                public_id=_row_public_id(keeper),
            )
        )

        for row in ordered[1:]:
            rid = _row_id(row)
            if not rid:
                continue
            if _row_locked(dict(row)):
                actions.append(
                    GeneratedCleanupAction(
                        action="protected",
                        reflection_id=rid,
                        reason="duplicate_but_locked",
                        owner_user_id=owner_user_id,
                        question=question,
                        answer_norm_hash=answer_norm_hash,
                        is_active=bool(row.get("is_active")),
                        public_id=_row_public_id(row),
                    )
                )
                continue
            is_active = bool(row.get("is_active"))
            if is_active and archive_active_duplicates:
                action = "archive"
                reason = "archive_exact_active_duplicate"
            elif is_active:
                action = "protected"
                reason = "active_duplicate_left_in_place"
            else:
                action = "delete"
                reason = "delete_inactive_duplicate_clone"
            actions.append(
                GeneratedCleanupAction(
                    action=action,
                    reflection_id=rid,
                    reason=reason,
                    owner_user_id=owner_user_id,
                    question=question,
                    answer_norm_hash=answer_norm_hash,
                    is_active=is_active,
                    public_id=_row_public_id(row),
                )
            )
    return actions



def summarize_unresolved_question_multi_answer_groups(
    rows: Sequence[Mapping[str, Any]],
    *,
    sample_limit: int = 20,
) -> List[Dict[str, Any]]:
    grouped: Dict[Tuple[str, str], List[Mapping[str, Any]]] = {}
    for row in rows or []:
        if str((row or {}).get("source_type") or "").strip() != "generated":
            continue
        if not bool((row or {}).get("is_active")):
            continue
        status = str((row or {}).get("status") or "").strip().lower()
        if status not in {"ready", "published"}:
            continue
        owner = str((row or {}).get("owner_user_id") or "").strip()
        question = str((row or {}).get("question") or "").strip()
        if not owner or not question:
            continue
        grouped.setdefault((owner, question), []).append(dict(row or {}))

    out: List[Dict[str, Any]] = []
    for (owner, question), items in grouped.items():
        unique_hashes: Dict[str, Dict[str, Any]] = {}
        for row in items:
            result = resolve_generated_reflection_display(row)
            norm_hash = str(getattr(result, "answer_norm_hash", "") or "").strip()
            if not norm_hash:
                continue
            unique_hashes.setdefault(norm_hash, {
                "topic_key": str(row.get("topic_key") or "").strip(),
                "public_id": _row_public_id(row),
                "answer_head": str(getattr(result, "answer_display_text", "") or row.get("answer") or "")[:120],
            })
        if len(unique_hashes) <= 1:
            continue
        out.append({
            "owner_user_id": owner,
            "question": question,
            "active_row_count": len(items),
            "unique_answer_count": len(unique_hashes),
            "answers": list(unique_hashes.values())[:5],
        })

    out.sort(key=lambda item: (-int(item.get("unique_answer_count") or 0), -int(item.get("active_row_count") or 0), str(item.get("question") or "")))
    return out[: max(1, int(sample_limit or 20))]



def simulate_cleanup_actions(
    rows: Sequence[Mapping[str, Any]],
    actions: Sequence[GeneratedCleanupAction],
) -> List[Dict[str, Any]]:
    by_id: Dict[str, Dict[str, Any]] = {_row_id(dict(row or {})): dict(row or {}) for row in rows or [] if _row_id(dict(row or {}))}
    for action in actions or []:
        rid = str(action.reflection_id or "").strip()
        if not rid or rid not in by_id:
            continue
        if action.action == "delete":
            by_id.pop(rid, None)
            continue
        if action.action == "archive":
            row = dict(by_id[rid])
            row["status"] = "archived"
            row["is_active"] = False
            by_id[rid] = row
    return list(by_id.values())


async def fetch_generated_reflection_rows(
    *,
    user_id: Optional[str] = None,
    batch_size: int = 500,
    max_rows: Optional[int] = None,
) -> List[Dict[str, Any]]:
    uid = str(user_id or "").strip()
    limit = max(1, min(int(batch_size or 500), 1000))
    cap = int(max_rows) if max_rows is not None else None

    all_rows: List[Dict[str, Any]] = []
    offset = 0
    while True:
        params: List[Tuple[str, str]] = [
            ("select", "id,public_id,owner_user_id,source_type,status,is_active,locked,topic_key,category,question,answer,content_json,updated_at,created_at"),
            ("source_type", "eq.generated"),
            ("order", "created_at.asc,id.asc"),
            ("limit", str(limit)),
            ("offset", str(offset)),
        ]
        if uid:
            params.append(("owner_user_id", f"eq.{uid}"))
        page = await _sb_get_json(f"/rest/v1/{REFLECTIONS_TABLE}", params=params, timeout=20.0)
        if not page:
            break
        all_rows.extend([dict(x) for x in page if isinstance(x, dict)])
        if cap is not None and len(all_rows) >= cap:
            return all_rows[:cap]
        if len(page) < limit:
            break
        offset += len(page)
    return all_rows


async def apply_generated_backfill_plans(plans: Sequence[GeneratedBackfillPlan]) -> List[str]:
    updated_ids: List[str] = []
    for plan in plans or []:
        rid = str(plan.reflection_id or "").strip()
        if not rid:
            continue
        rows = await _sb_patch_json(
            f"/rest/v1/{REFLECTIONS_TABLE}",
            params=[("id", f"eq.{rid}")],
            json_body={"content_json": dict(plan.content_json)},
            timeout=15.0,
            prefer="return=minimal",
        )
        updated_ids.append(rid)
    return updated_ids


async def apply_generated_cleanup_actions(actions: Sequence[GeneratedCleanupAction]) -> Dict[str, List[str]]:
    archived_ids: List[str] = []
    deleted_ids: List[str] = []
    for action in actions or []:
        rid = str(action.reflection_id or "").strip()
        if not rid:
            continue
        if action.action == "archive":
            await _sb_patch_json(
                f"/rest/v1/{REFLECTIONS_TABLE}",
                params=[("id", f"eq.{rid}")],
                json_body={
                    "status": "archived",
                    "is_active": False,
                    "published_at": None,
                },
                timeout=10.0,
                prefer="return=minimal",
            )
            archived_ids.append(rid)
        elif action.action == "delete":
            await _sb_delete(
                f"/rest/v1/{REFLECTIONS_TABLE}",
                params=[("id", f"eq.{rid}")],
                timeout=10.0,
                prefer="return=minimal",
            )
            deleted_ids.append(rid)
    return {
        "archived_ids": archived_ids,
        "deleted_ids": deleted_ids,
    }


async def run_generated_reflection_backfill_cleanup(
    *,
    user_id: Optional[str] = None,
    batch_size: int = 500,
    max_rows: Optional[int] = None,
    apply: bool = False,
    do_backfill: bool = True,
    do_cleanup: bool = True,
    archive_active_duplicates: bool = True,
    sample_limit: int = 20,
) -> Dict[str, Any]:
    rows = await fetch_generated_reflection_rows(user_id=user_id, batch_size=batch_size, max_rows=max_rows)

    backfill_plans: List[GeneratedBackfillPlan] = []
    effective_rows: List[Dict[str, Any]] = []
    plan_by_id: Dict[str, GeneratedBackfillPlan] = {}
    for row in rows:
        plan = build_generated_reflection_backfill_plan(row) if do_backfill else None
        rid = _row_id(row)
        if plan is not None and rid:
            backfill_plans.append(plan)
            plan_by_id[rid] = plan
            patched_row = dict(row)
            patched_row["content_json"] = dict(plan.content_json)
            effective_rows.append(patched_row)
        else:
            effective_rows.append(dict(row))

    cleanup_actions = plan_generated_reflection_duplicate_cleanup(
        effective_rows,
        archive_active_duplicates=archive_active_duplicates,
    ) if do_cleanup else []
    actionable_cleanup = [a for a in cleanup_actions if a.action in {"archive", "delete"}]

    simulated_rows = simulate_cleanup_actions(effective_rows, cleanup_actions)
    unresolved_groups = summarize_unresolved_question_multi_answer_groups(simulated_rows, sample_limit=sample_limit)

    applied_backfill_ids: List[str] = []
    applied_cleanup: Dict[str, List[str]] = {"archived_ids": [], "deleted_ids": []}
    if apply:
        if do_backfill and backfill_plans:
            applied_backfill_ids = await apply_generated_backfill_plans(backfill_plans)
        if do_cleanup and actionable_cleanup:
            applied_cleanup = await apply_generated_cleanup_actions(actionable_cleanup)

    cleanup_counts = {
        "keep": len([a for a in cleanup_actions if a.action == "keep"]),
        "protected": len([a for a in cleanup_actions if a.action == "protected"]),
        "archive": len([a for a in cleanup_actions if a.action == "archive"]),
        "delete": len([a for a in cleanup_actions if a.action == "delete"]),
    }

    backfill_reason_counts: Dict[str, int] = {}
    for plan in backfill_plans:
        for reason in [x.strip() for x in str(plan.reason or "").split(",") if x.strip()]:
            backfill_reason_counts[reason] = int(backfill_reason_counts.get(reason) or 0) + 1

    return {
        "user_id": str(user_id or "").strip() or None,
        "apply": bool(apply),
        "scanned_row_count": len(rows),
        "backfill": {
            "planned_count": len(backfill_plans),
            "applied_count": len(applied_backfill_ids),
            "reason_counts": backfill_reason_counts,
            "sample_reflection_ids": [plan.reflection_id for plan in backfill_plans[:10]],
        },
        "cleanup": {
            "planned_action_count": len(actionable_cleanup),
            "applied_archive_count": len(applied_cleanup.get("archived_ids") or []),
            "applied_delete_count": len(applied_cleanup.get("deleted_ids") or []),
            "counts": cleanup_counts,
            "sample_actions": [
                {
                    "action": a.action,
                    "reflection_id": a.reflection_id,
                    "reason": a.reason,
                    "question": a.question,
                    "public_id": a.public_id,
                }
                for a in actionable_cleanup[:15]
            ],
        },
        "unresolved_question_multi_answer_groups": {
            "count": len(unresolved_groups),
            "samples": unresolved_groups,
        },
    }


__all__ = [
    "GeneratedBackfillPlan",
    "GeneratedCleanupAction",
    "apply_generated_backfill_plans",
    "apply_generated_cleanup_actions",
    "build_generated_reflection_backfill_plan",
    "fetch_generated_reflection_rows",
    "plan_generated_reflection_duplicate_cleanup",
    "run_generated_reflection_backfill_cleanup",
    "simulate_cleanup_actions",
    "summarize_unresolved_question_multi_answer_groups",
]
