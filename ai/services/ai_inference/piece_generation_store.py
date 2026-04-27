# -*- coding: utf-8 -*-
"""piece_generation_store.py

Premium Reflection store layer (v1)
===================================

役割
----
Reflection Engine が返した generation plan を、`public.mymodel_reflections` に
"DRAFT / inactive" で stage 保存する保存レイヤー。

このファイルは国家機構上の「Reflections生成局の保存担当」であり、以下のみを担当する。

- 既存 generated reflections の取得
- generation plan の stage 保存（create / update）
- topic 不在 reflection の deactivate
- inspection 通過後の promote / fail / reject
- active generated reflection 上限の整理（capacity policy）

このファイルがやらないこと
--------------------------
- topic detection
- question / answer 生成
- embedding
- inspection 判定
- publish 判定
- template（MyModelCreate）Reflection の生成

設計原則
--------
- generated reflections のみを扱う
- stage 保存は `status=draft`, `is_active=false`
- update は上書きではなく staged row を新規作成する
- inspection pass 時に新 row を `ready + active` にし、旧 active row を archive する
- topic 不在は即 `archived + inactive`
- active 上限は generated reflections に対してのみ適用する
"""

from __future__ import annotations

from datetime import datetime, timezone
import logging
import os
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

import httpx

from piece_generated_display import (
    apply_generated_display_to_content_json,
    build_generated_reflection_display,
    resolve_generated_reflection_display,
)
from piece_generated_identity import compute_generated_question_q_key

logger = logging.getLogger("astor_reflection_store")

SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or "").strip()

REFLECTIONS_TABLE = (os.getenv("MYMODEL_REFLECTIONS_TABLE") or "mymodel_reflections").strip() or "mymodel_reflections"
REFLECTIONS_READ_TABLE = (
    os.getenv("COCOLON_PIECES_READ_TABLE")
    or os.getenv("COCOLON_MYMODEL_REFLECTIONS_READ_TABLE")
    or os.getenv("MYMODEL_REFLECTIONS_READ_TABLE")
    or "pieces"
).strip() or "pieces"
# This store only reads QnA metrics for capacity decisions; use the current-name
# backend-readonly bridge view. Metrics write paths live elsewhere and remain legacy.
QNA_METRICS_READ_TABLE = (
    os.getenv("COCOLON_PIECE_METRICS_READ_TABLE")
    or os.getenv("COCOLON_MYMODEL_QNA_METRICS_READ_TABLE")
    or "piece_metrics"
).strip() or "piece_metrics"
DISCOVERY_LOGS_TABLE = (
    os.getenv("COCOLON_MYMODEL_QNA_DISCOVERY_LOGS_TABLE") or "mymodel_qna_discovery_logs"
).strip() or "mymodel_qna_discovery_logs"

DEFAULT_MAX_ACTIVE_GENERATED = int(os.getenv("REFLECTION_MAX_ACTIVE_GENERATED", "50") or "50")
DEFAULT_MAX_LOCKED_GENERATED = int(os.getenv("REFLECTION_MAX_LOCKED_GENERATED", "10") or "10")
DEFAULT_EVICTION_POLICY = (os.getenv("REFLECTION_EVICTION_POLICY") or "oldest").strip() or "oldest"
LEGACY_GENERATED_REFLECTIONS_RETIRED = (os.getenv("LEGACY_GENERATED_REFLECTIONS_RETIRED") or "true").strip().lower() in {"1", "true", "yes", "on"}


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------
def _now_iso_z() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _has_supabase_config() -> bool:
    return bool(SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY)


def _sb_headers_json(*, prefer: str = "return=minimal") -> Dict[str, str]:
    return {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": prefer,
    }


def _sb_headers(*, prefer: str = "") -> Dict[str, str]:
    h = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


async def _sb_get_json(path: str, *, params: List[Tuple[str, str]], timeout: float = 8.0) -> List[Dict[str, Any]]:
    if not _has_supabase_config():
        raise RuntimeError("Supabase config missing")
    url = f"{SUPABASE_URL}{path}"
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(url, headers=_sb_headers(), params=params)
    if resp.status_code not in (200, 206):
        raise RuntimeError(f"Supabase GET failed: {resp.status_code} {(resp.text or '')[:800]}")
    try:
        data = resp.json()
    except Exception:
        return []
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    return []


async def _sb_patch_json(
    path: str,
    *,
    params: List[Tuple[str, str]],
    json_body: Any,
    timeout: float = 8.0,
    prefer: str = "return=representation",
) -> List[Dict[str, Any]]:
    if not _has_supabase_config():
        raise RuntimeError("Supabase config missing")
    url = f"{SUPABASE_URL}{path}"
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.patch(url, headers=_sb_headers_json(prefer=prefer), params=params, json=json_body)
    if resp.status_code not in (200, 204):
        raise RuntimeError(f"Supabase PATCH failed: {resp.status_code} {(resp.text or '')[:800]}")
    if resp.status_code == 204:
        return []
    try:
        data = resp.json()
    except Exception:
        return []
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    return []


async def _sb_post_json(
    path: str,
    *,
    json_body: Any,
    timeout: float = 8.0,
    prefer: str = "return=representation",
) -> List[Dict[str, Any]]:
    if not _has_supabase_config():
        raise RuntimeError("Supabase config missing")
    url = f"{SUPABASE_URL}{path}"
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, headers=_sb_headers_json(prefer=prefer), json=json_body)
    if resp.status_code not in (200, 201, 204):
        raise RuntimeError(f"Supabase POST failed: {resp.status_code} {(resp.text or '')[:800]}")
    if resp.status_code == 204:
        return []
    try:
        data = resp.json()
    except Exception:
        return []
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    return []


async def _sb_delete(
    path: str,
    *,
    params: List[Tuple[str, str]],
    timeout: float = 8.0,
    prefer: str = "return=minimal",
) -> None:
    if not _has_supabase_config():
        raise RuntimeError("Supabase config missing")
    url = f"{SUPABASE_URL}{path}"
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.delete(url, headers=_sb_headers(prefer=prefer), params=params)
    if resp.status_code not in (200, 204):
        raise RuntimeError(f"Supabase DELETE failed: {resp.status_code} {(resp.text or '')[:800]}")


async def _sb_count(path: str, *, params: List[Tuple[str, str]], timeout: float = 8.0) -> int:
    p = list(params)
    p.insert(0, ("select", "id"))
    p.append(("limit", "0"))
    url = f"{SUPABASE_URL}{path}"
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(url, headers=_sb_headers(prefer="count=exact"), params=p)
    if resp.status_code not in (200, 206):
        raise RuntimeError(f"Supabase COUNT failed: {resp.status_code} {(resp.text or '')[:800]}")
    cr = resp.headers.get("content-range") or resp.headers.get("Content-Range") or ""
    try:
        if "/" not in cr:
            return 0
        total = cr.split("/", 1)[1].strip()
        return 0 if total in ("", "*") else int(total)
    except Exception:
        return 0


def _quoted_in(values: Iterable[str]) -> str:
    vals = sorted({str(v).strip() for v in values if str(v).strip()})
    inner = ",".join([f'"{v}"' for v in vals])
    return f"in.({inner})"


# ---------------------------------------------------------------------------
# serialization helpers
# ---------------------------------------------------------------------------
def _row_id(row: Dict[str, Any]) -> str:
    return str(row.get("id") or "").strip()


def _row_public_id(row: Dict[str, Any]) -> str:
    return str(row.get("public_id") or "").strip()


def _row_q_key(row: Dict[str, Any]) -> str:
    qk = str(row.get("q_key") or "").strip()
    if qk:
        return qk
    return compute_generated_question_q_key(row.get("question"))


def _row_locked(row: Dict[str, Any]) -> bool:
    v = row.get("locked")
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    return str(v or "").strip().lower() in {"1", "true", "t", "yes", "y", "on"}


def _generated_public_group_sort_key(row: Dict[str, Any]) -> Tuple[str, str, str]:
    return (
        str(row.get("updated_at") or row.get("created_at") or "").strip(),
        str(row.get("created_at") or "").strip(),
        _row_id(row),
    )


def _build_content_json(
    *,
    topic_key: str,
    q_key: str,
    category: str,
    question: str,
    answer: str,
    source_snapshot_id: str,
    source_hash: str,
    source_refs: Sequence[Dict[str, Any]],
    topic_summary_text: Optional[str],
    topic_embedding: Optional[Sequence[float]],
    focus_key: Optional[str],
    previous_reflection_id: Optional[str] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "version": "premium_reflection.v1",
        "source_type": "generated",
        "topic_key": str(topic_key or "").strip(),
        "q_key": str(q_key or "").strip() or None,
        "category": str(category or "").strip(),
        "question": str(question or "").strip(),
        "answer": str(answer or "").strip(),
        "source_snapshot_id": str(source_snapshot_id or "").strip() or None,
        "source_hash": str(source_hash or "").strip() or None,
        "source_refs": list(source_refs or []),
        "topic_summary_text": str(topic_summary_text or "").strip() or None,
        "topic_embedding": [float(x) for x in (topic_embedding or [])],
        "focus_key": str(focus_key or "").strip() or None,
    }
    if previous_reflection_id:
        payload["previous_reflection_id"] = str(previous_reflection_id)
    return payload


# ---------------------------------------------------------------------------
# fetch helpers
# ---------------------------------------------------------------------------
async def fetch_active_generated_reflections(*, user_id: str) -> List[Dict[str, Any]]:
    uid = str(user_id or "").strip()
    if not uid:
        return []
    rows = await _sb_get_json(
        f"/rest/v1/{REFLECTIONS_READ_TABLE}",
        params=[
            ("select", "*"),
            ("owner_user_id", f"eq.{uid}"),
            ("source_type", "eq.generated"),
            ("is_active", "eq.true"),
            ("order", "updated_at.desc"),
            ("limit", "200"),
        ],
        timeout=10.0,
    )
    return rows


async def fetch_staged_generated_reflections(*, user_id: str, source_hash: Optional[str] = None) -> List[Dict[str, Any]]:
    uid = str(user_id or "").strip()
    if not uid:
        return []
    params: List[Tuple[str, str]] = [
        ("select", "*"),
        ("owner_user_id", f"eq.{uid}"),
        ("source_type", "eq.generated"),
        ("status", "eq.draft"),
        ("is_active", "eq.false"),
        ("order", "updated_at.desc"),
        ("limit", "200"),
    ]
    sh = str(source_hash or "").strip()
    if sh:
        params.append(("source_hash", f"eq.{sh}"))
    return await _sb_get_json(f"/rest/v1/{REFLECTIONS_READ_TABLE}", params=params, timeout=10.0)


async def fetch_lock_count(*, user_id: str) -> int:
    uid = str(user_id or "").strip()
    if not uid:
        return 0
    return await _sb_count(
        f"/rest/v1/{REFLECTIONS_READ_TABLE}",
        params=[
            ("owner_user_id", f"eq.{uid}"),
            ("source_type", "eq.generated"),
            ("is_active", "eq.true"),
            ("locked", "eq.true"),
        ],
        timeout=8.0,
    )


async def _fetch_reflection_by_id(reflection_id: str) -> Optional[Dict[str, Any]]:
    rid = str(reflection_id or "").strip()
    if not rid:
        return None
    rows = await _sb_get_json(
        f"/rest/v1/{REFLECTIONS_READ_TABLE}",
        params=[
            ("select", "*"),
            ("id", f"eq.{rid}"),
            ("limit", "1"),
        ],
        timeout=8.0,
    )
    return rows[0] if rows else None


async def _find_existing_staged_generated_row(*, user_id: str, q_key: str, topic_key: str, source_hash: str) -> Optional[Dict[str, Any]]:
    uid = str(user_id or "").strip()
    qk = str(q_key or "").strip()
    tk = str(topic_key or "").strip()
    sh = str(source_hash or "").strip()
    if not uid or not sh:
        return None

    query_sets: List[List[Tuple[str, str]]] = []
    if qk:
        query_sets.append([
            ("select", "*"),
            ("owner_user_id", f"eq.{uid}"),
            ("source_type", "eq.generated"),
            ("q_key", f"eq.{qk}"),
            ("source_hash", f"eq.{sh}"),
            ("status", "eq.draft"),
            ("is_active", "eq.false"),
            ("order", "updated_at.desc"),
            ("limit", "1"),
        ])
    if tk:
        query_sets.append([
            ("select", "*"),
            ("owner_user_id", f"eq.{uid}"),
            ("source_type", "eq.generated"),
            ("topic_key", f"eq.{tk}"),
            ("source_hash", f"eq.{sh}"),
            ("status", "eq.draft"),
            ("is_active", "eq.false"),
            ("order", "updated_at.desc"),
            ("limit", "1"),
        ])

    for params in query_sets:
        rows = await _sb_get_json(
            f"/rest/v1/{REFLECTIONS_READ_TABLE}",
            params=params,
            timeout=8.0,
        )
        if rows:
            return rows[0]
    return None


async def _fetch_active_generated_topic_rows(*, user_id: str, topic_key: str, exclude_id: Optional[str] = None) -> List[Dict[str, Any]]:
    uid = str(user_id or "").strip()
    tk = str(topic_key or "").strip()
    ex = str(exclude_id or "").strip()
    if not uid or not tk:
        return []
    rows = await _sb_get_json(
        f"/rest/v1/{REFLECTIONS_READ_TABLE}",
        params=[
            ("select", "*"),
            ("owner_user_id", f"eq.{uid}"),
            ("source_type", "eq.generated"),
            ("topic_key", f"eq.{tk}"),
            ("is_active", "eq.true"),
            ("order", "updated_at.desc"),
            ("limit", "20"),
        ],
        timeout=8.0,
    )
    if ex:
        rows = [r for r in rows if _row_id(r) != ex]
    return rows


async def _fetch_active_generated_public_group_rows(
    *,
    user_id: str,
    q_key: str,
    question: str,
    exclude_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    uid = str(user_id or "").strip()
    qk = str(q_key or "").strip()
    q = str(question or "").strip()
    ex = str(exclude_id or "").strip()
    if not uid:
        return []

    # Public/generated reflections are unique by (owner_user_id, q_key).
    # question is used only as a legacy fallback when q_key is absent.

    merged: Dict[str, Dict[str, Any]] = {}
    query_sets: List[List[Tuple[str, str]]] = []
    if qk:
        query_sets.append([
            ("select", "*"),
            ("owner_user_id", f"eq.{uid}"),
            ("source_type", "eq.generated"),
            ("q_key", f"eq.{qk}"),
            ("is_active", "eq.true"),
            ("order", "updated_at.desc"),
            ("limit", "50"),
        ])
    if q:
        query_sets.append([
            ("select", "*"),
            ("owner_user_id", f"eq.{uid}"),
            ("source_type", "eq.generated"),
            ("question", f"eq.{q}"),
            ("is_active", "eq.true"),
            ("order", "updated_at.desc"),
            ("limit", "50"),
        ])

    for params in query_sets:
        rows = await _sb_get_json(f"/rest/v1/{REFLECTIONS_READ_TABLE}", params=params, timeout=8.0)
        for row in rows:
            rid = _row_id(row)
            if not rid or rid == ex:
                continue
            merged[rid] = row

    ordered = sorted(merged.values(), key=_generated_public_group_sort_key, reverse=True)
    return ordered


def _skip_same_as_active_marker(*, active_row: Dict[str, Any], answer_norm_hash: str) -> Dict[str, Any]:
    return {
        "_stage_action": "skip_same_as_active",
        "id": _row_id(active_row),
        "public_id": _row_public_id(active_row),
        "answer_norm_hash": str(answer_norm_hash or "").strip(),
    }


async def _maybe_skip_same_as_active(
    *,
    user_id: str,
    q_key: str,
    question: str,
    proposal_display_result: Any,
    previous_reflection_id: Optional[str],
) -> Optional[Dict[str, Any]]:
    active_rows = await _fetch_active_generated_public_group_rows(
        user_id=user_id,
        q_key=q_key,
        question=question,
        exclude_id=str(previous_reflection_id or "").strip() or None,
    )
    proposal_question = str(question or "").strip()
    proposal_hash = str(getattr(proposal_display_result, "answer_norm_hash", "") or "").strip()
    if not proposal_question or not proposal_hash:
        return None

    for active_row in active_rows:
        active_question = str((active_row or {}).get("question") or "").strip()
        if active_question != proposal_question:
            continue
        active_display_result = resolve_generated_reflection_display(active_row)
        active_hash = str(getattr(active_display_result, "answer_norm_hash", "") or "").strip()
        if active_hash and active_hash == proposal_hash:
            return _skip_same_as_active_marker(
                active_row=active_row,
                answer_norm_hash=proposal_hash,
            )
    return None


# ---------------------------------------------------------------------------
# stage helpers
# ---------------------------------------------------------------------------
async def _upsert_staged_generated_row(
    *,
    user_id: str,
    topic_key: str,
    q_key: str,
    category: str,
    question: str,
    answer: str,
    source_snapshot_id: str,
    source_hash: str,
    source_refs: Sequence[Dict[str, Any]],
    topic_summary_text: Optional[str],
    topic_embedding: Optional[Sequence[float]],
    focus_key: Optional[str],
    previous_reflection_id: Optional[str],
    locked: bool,
    lock_note: Optional[str],
) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    tk = str(topic_key or "").strip()
    qk = str(q_key or "").strip() or compute_generated_question_q_key(question)
    if not uid or not tk:
        raise ValueError("user_id and topic_key are required")

    display_updated_at = _now_iso_z()
    display_result = build_generated_reflection_display(
        question=question,
        raw_answer=answer,
        category=category,
        focus_key=focus_key,
        topic_summary_text=topic_summary_text,
    )

    skip_marker = await _maybe_skip_same_as_active(
        user_id=uid,
        q_key=qk,
        question=question,
        proposal_display_result=display_result,
        previous_reflection_id=previous_reflection_id,
    )
    if skip_marker is not None:
        return skip_marker

    existing = await _find_existing_staged_generated_row(user_id=uid, q_key=qk, topic_key=tk, source_hash=source_hash)
    content_json = _build_content_json(
        topic_key=tk,
        q_key=qk,
        category=category,
        question=question,
        answer=answer,
        source_snapshot_id=source_snapshot_id,
        source_hash=source_hash,
        source_refs=source_refs,
        topic_summary_text=topic_summary_text,
        topic_embedding=topic_embedding,
        focus_key=focus_key,
        previous_reflection_id=previous_reflection_id,
    )
    content_json = apply_generated_display_to_content_json(
        content_json,
        result=display_result,
        display_updated_at=display_updated_at,
    )

    payload = {
        "owner_user_id": uid,
        "source_type": "generated",
        "status": "draft",
        "is_active": False,
        "topic_key": tk,
        "q_key": qk,
        "category": str(category or "").strip() or None,
        "question": str(question or "").strip(),
        "answer": str(answer or "").strip(),
        "content_json": content_json,
        "source_snapshot_id": str(source_snapshot_id or "").strip() or None,
        "source_hash": str(source_hash or "").strip() or None,
        "source_refs": list(source_refs or []),
        "locked": bool(locked),
        "lock_note": str(lock_note or "").strip() or None,
        "published_at": None,
    }

    if existing:
        rid = _row_id(existing)
        rows = await _sb_patch_json(
            f"/rest/v1/{REFLECTIONS_TABLE}",
            params=[("id", f"eq.{rid}")],
            json_body=payload,
            timeout=10.0,
            prefer="return=representation",
        )
        return rows[0] if rows else existing

    rows = await _sb_post_json(
        f"/rest/v1/{REFLECTIONS_TABLE}",
        json_body=payload,
        timeout=10.0,
        prefer="return=representation",
    )
    if not rows:
        raise RuntimeError("Failed to insert staged generated reflection")
    return rows[0]


async def _stage_create(*, user_id: str, proposal: Dict[str, Any]) -> Dict[str, Any]:
    return await _upsert_staged_generated_row(
        user_id=user_id,
        topic_key=str(proposal.get("topic_key") or "").strip(),
        q_key=str(proposal.get("q_key") or "").strip(),
        category=str(proposal.get("category") or "").strip(),
        question=str(proposal.get("question") or "").strip(),
        answer=str(proposal.get("answer") or "").strip(),
        source_snapshot_id=str(proposal.get("source_snapshot_id") or "").strip(),
        source_hash=str(proposal.get("source_hash") or "").strip(),
        source_refs=proposal.get("source_refs") or [],
        topic_summary_text=proposal.get("topic_summary_text"),
        topic_embedding=proposal.get("topic_embedding") or [],
        focus_key=proposal.get("focus_key"),
        previous_reflection_id=None,
        locked=False,
        lock_note=None,
    )


async def _stage_update(*, user_id: str, proposal: Dict[str, Any]) -> Dict[str, Any]:
    previous_id = str(proposal.get("reflection_id") or "").strip()
    previous = await _fetch_reflection_by_id(previous_id) if previous_id else None

    return await _upsert_staged_generated_row(
        user_id=user_id,
        topic_key=str(proposal.get("topic_key") or "").strip(),
        q_key=str(proposal.get("q_key") or "").strip(),
        category=str(proposal.get("category") or "").strip(),
        question=str(proposal.get("question") or "").strip(),
        answer=str(proposal.get("answer") or "").strip(),
        source_snapshot_id=str(proposal.get("source_snapshot_id") or "").strip(),
        source_hash=str(proposal.get("source_hash") or "").strip(),
        source_refs=proposal.get("source_refs") or [],
        topic_summary_text=proposal.get("topic_summary_text"),
        topic_embedding=proposal.get("topic_embedding") or [],
        focus_key=proposal.get("focus_key"),
        previous_reflection_id=previous_id or None,
        locked=_row_locked(previous or {}),
        lock_note=str((previous or {}).get("lock_note") or "").strip() or None,
    )


async def _apply_deactivates(*, user_id: str, deactivates: Sequence[Dict[str, Any]]) -> List[str]:
    uid = str(user_id or "").strip()
    out: List[str] = []
    if not uid:
        return out

    for item in deactivates or []:
        rid = str((item or {}).get("reflection_id") or "").strip()
        if not rid:
            continue
        rows = await _sb_patch_json(
            f"/rest/v1/{REFLECTIONS_TABLE}",
            params=[
                ("id", f"eq.{rid}"),
                ("owner_user_id", f"eq.{uid}"),
                ("source_type", "eq.generated"),
                ("is_active", "eq.true"),
            ],
            json_body={
                "status": "archived",
                "is_active": False,
                "published_at": None,
            },
            timeout=8.0,
            prefer="return=representation",
        )
        if rows:
            out.extend([_row_id(r) for r in rows if _row_id(r)])
    return out


async def stage_generation_plan(
    *,
    user_id: str,
    snapshot_id: str,
    source_hash: str,
    generation_plan: Dict[str, Any],
) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    sid = str(snapshot_id or "").strip()
    sh = str(source_hash or "").strip()
    if not uid:
        raise ValueError("user_id is required")
    if not sid:
        raise ValueError("snapshot_id is required")
    if not sh:
        raise ValueError("source_hash is required")

    creates = generation_plan.get("creates") or []
    updates = generation_plan.get("updates") or []
    deactivates = generation_plan.get("deactivates") or []

    created_ids: List[str] = []
    updated_ids: List[str] = []
    inspection_targets: List[str] = []
    skipped_same_as_active_ids: List[str] = []

    if LEGACY_GENERATED_REFLECTIONS_RETIRED:
        deactivated_ids = await _apply_deactivates(user_id=uid, deactivates=deactivates)
        return {
            "user_id": uid,
            "snapshot_id": sid,
            "source_hash": sh,
            "created_ids": [],
            "updated_ids": [],
            "deactivated_ids": deactivated_ids,
            "skipped_same_as_active_ids": [],
            "inspection_targets": [],
            "retired": True,
            "stats": {
                "created_count": 0,
                "updated_count": 0,
                "deactivated_count": len(deactivated_ids),
                "skipped_same_as_active_count": 0,
                "inspection_target_count": 0,
            },
        }

    for proposal in creates:
        proposal = dict(proposal or {})
        proposal.setdefault("source_snapshot_id", sid)
        proposal.setdefault("source_hash", sh)
        row = await _stage_create(user_id=uid, proposal=proposal)
        if str((row or {}).get("_stage_action") or "").strip() == "skip_same_as_active":
            skipped_id = _row_id(row)
            if skipped_id:
                skipped_same_as_active_ids.append(skipped_id)
            continue
        rid = _row_id(row)
        if rid:
            created_ids.append(rid)
            inspection_targets.append(rid)

    for proposal in updates:
        proposal = dict(proposal or {})
        proposal.setdefault("source_snapshot_id", sid)
        proposal.setdefault("source_hash", sh)
        row = await _stage_update(user_id=uid, proposal=proposal)
        if str((row or {}).get("_stage_action") or "").strip() == "skip_same_as_active":
            skipped_id = _row_id(row)
            if skipped_id:
                skipped_same_as_active_ids.append(skipped_id)
            continue
        rid = _row_id(row)
        if rid:
            updated_ids.append(rid)
            inspection_targets.append(rid)

    deactivated_ids = await _apply_deactivates(user_id=uid, deactivates=deactivates)

    return {
        "user_id": uid,
        "snapshot_id": sid,
        "source_hash": sh,
        "created_ids": created_ids,
        "updated_ids": updated_ids,
        "deactivated_ids": deactivated_ids,
        "skipped_same_as_active_ids": _unique_keep_order(skipped_same_as_active_ids),
        "inspection_targets": _unique_keep_order(inspection_targets),
        "stats": {
            "created_count": len(created_ids),
            "updated_count": len(updated_ids),
            "deactivated_count": len(deactivated_ids),
            "skipped_same_as_active_count": len(_unique_keep_order(skipped_same_as_active_ids)),
            "inspection_target_count": len(_unique_keep_order(inspection_targets)),
        },
    }


# ---------------------------------------------------------------------------
# promote / reject / fail
# ---------------------------------------------------------------------------
async def promote_reflection(
    *,
    reflection_id: str,
    max_active: int = DEFAULT_MAX_ACTIVE_GENERATED,
    eviction_policy: str = DEFAULT_EVICTION_POLICY,
) -> Dict[str, Any]:
    row = await _fetch_reflection_by_id(reflection_id)
    if not row:
        raise ValueError("reflection not found")

    if LEGACY_GENERATED_REFLECTIONS_RETIRED:
        rid = _row_id(row)
        retired_rows = await _sb_patch_json(
            f"/rest/v1/{REFLECTIONS_TABLE}",
            params=[("id", f"eq.{rid}")],
            json_body={
                "status": "archived",
                "is_active": False,
                "published_at": None,
            },
            timeout=8.0,
            prefer="return=representation",
        )
        retired_row = retired_rows[0] if retired_rows else {**row, "status": "archived", "is_active": False, "published_at": None}
        return {
            "promoted_id": rid,
            "previous_archived_ids": [],
            "post_verify_archived_ids": [],
            "capacity": {
                "evicted_ids": [],
                "active_count": 0,
                "max_active": int(max_active),
                "policy": str(eviction_policy or DEFAULT_EVICTION_POLICY),
            },
            "retired": True,
            "row": retired_row,
        }

    uid = str(row.get("owner_user_id") or "").strip()
    topic_key = str(row.get("topic_key") or "").strip()
    question = str(row.get("question") or "").strip()
    q_key = _row_q_key(row)
    rid = _row_id(row)
    if not uid or not topic_key or not rid:
        raise ValueError("reflection row missing owner/topic/id")
    if str(row.get("source_type") or "") != "generated":
        raise ValueError("promote_reflection only supports generated reflections")

    previous_rows = await _fetch_active_generated_public_group_rows(
        user_id=uid,
        q_key=q_key,
        question=question,
        exclude_id=rid,
    )

    previous_ids: List[str] = []
    for prev in previous_rows:
        pid = _row_id(prev)
        if not pid:
            continue
        previous_ids.append(pid)
        await _sb_patch_json(
            f"/rest/v1/{REFLECTIONS_TABLE}",
            params=[("id", f"eq.{pid}")],
            json_body={
                "status": "archived",
                "is_active": False,
                "published_at": None,
            },
            timeout=8.0,
            prefer="return=minimal",
        )

    promoted_rows = await _sb_patch_json(
        f"/rest/v1/{REFLECTIONS_TABLE}",
        params=[("id", f"eq.{rid}")],
        json_body={
            "status": "ready",
            "is_active": True,
            "q_key": q_key,
        },
        timeout=8.0,
        prefer="return=representation",
    )
    promoted = promoted_rows[0] if promoted_rows else row

    post_rows = await _fetch_active_generated_public_group_rows(
        user_id=uid,
        q_key=q_key,
        question=question,
        exclude_id=None,
    )
    ordered_post_rows = sorted(post_rows, key=_generated_public_group_sort_key, reverse=True)
    post_verify_archived_ids: List[str] = []
    for extra in ordered_post_rows:
        eid = _row_id(extra)
        if not eid or eid == rid:
            continue
        await _sb_patch_json(
            f"/rest/v1/{REFLECTIONS_TABLE}",
            params=[("id", f"eq.{eid}")],
            json_body={
                "status": "archived",
                "is_active": False,
                "published_at": None,
            },
            timeout=8.0,
            prefer="return=minimal",
        )
        post_verify_archived_ids.append(eid)

    capacity = await enforce_capacity_policy(user_id=uid, max_active=max_active, eviction_policy=eviction_policy)

    return {
        "promoted_id": rid,
        "previous_archived_ids": previous_ids,
        "post_verify_archived_ids": post_verify_archived_ids,
        "capacity": capacity,
        "row": promoted,
    }


async def reject_reflection(*, reflection_id: str) -> Dict[str, Any]:
    rid = str(reflection_id or "").strip()
    if not rid:
        raise ValueError("reflection_id is required")
    rows = await _sb_patch_json(
        f"/rest/v1/{REFLECTIONS_TABLE}",
        params=[("id", f"eq.{rid}")],
        json_body={
            "status": "rejected",
            "is_active": False,
            "published_at": None,
        },
        timeout=8.0,
        prefer="return=representation",
    )
    return rows[0] if rows else {"id": rid, "status": "rejected", "is_active": False}


async def fail_reflection(*, reflection_id: str) -> Dict[str, Any]:
    rid = str(reflection_id or "").strip()
    if not rid:
        raise ValueError("reflection_id is required")
    rows = await _sb_patch_json(
        f"/rest/v1/{REFLECTIONS_TABLE}",
        params=[("id", f"eq.{rid}")],
        json_body={
            "status": "failed",
            "is_active": False,
            "published_at": None,
        },
        timeout=8.0,
        prefer="return=representation",
    )
    return rows[0] if rows else {"id": rid, "status": "failed", "is_active": False}


# ---------------------------------------------------------------------------
# capacity policy
# ---------------------------------------------------------------------------
async def _fetch_generated_active_rows_for_capacity(*, user_id: str) -> List[Dict[str, Any]]:
    uid = str(user_id or "").strip()
    if not uid:
        return []
    rows = await _sb_get_json(
        f"/rest/v1/{REFLECTIONS_READ_TABLE}",
        params=[
            ("select", "id,public_id,owner_user_id,topic_key,locked,updated_at,created_at,status,is_active,content_json"),
            ("owner_user_id", f"eq.{uid}"),
            ("source_type", "eq.generated"),
            ("status", "eq.ready"),
            ("is_active", "eq.true"),
            ("order", "updated_at.asc"),
            ("limit", "500"),
        ],
        timeout=10.0,
    )
    return rows


async def _fetch_resonance_counts_by_public_ids(public_ids: Sequence[str]) -> Dict[str, int]:
    ids = [str(x).strip() for x in public_ids if str(x).strip()]
    if not ids:
        return {}
    rows = await _sb_get_json(
        f"/rest/v1/{QNA_METRICS_READ_TABLE}",
        params=[
            ("select", "q_instance_id,resonances"),
            ("q_instance_id", _quoted_in(set(ids))),
            ("limit", str(max(1, len(ids)))),
        ],
        timeout=8.0,
    )
    out: Dict[str, int] = {}
    for r in rows:
        pid = str(r.get("q_instance_id") or "").strip()
        if not pid:
            continue
        try:
            out[pid] = int(r.get("resonances") or 0)
        except Exception:
            out[pid] = 0
    return out


async def _fetch_discovery_counts_by_public_ids(public_ids: Sequence[str]) -> Dict[str, int]:
    ids = [str(x).strip() for x in public_ids if str(x).strip()]
    if not ids:
        return {}
    rows = await _sb_get_json(
        f"/rest/v1/{DISCOVERY_LOGS_TABLE}",
        params=[
            ("select", "q_instance_id"),
            ("q_instance_id", _quoted_in(set(ids))),
            ("limit", "50000"),
        ],
        timeout=8.0,
    )
    out: Dict[str, int] = {}
    for r in rows:
        pid = str(r.get("q_instance_id") or "").strip()
        if not pid:
            continue
        out[pid] = int(out.get(pid) or 0) + 1
    return out


async def enforce_capacity_policy(
    *,
    user_id: str,
    max_active: int = DEFAULT_MAX_ACTIVE_GENERATED,
    eviction_policy: str = DEFAULT_EVICTION_POLICY,
) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    if not uid:
        return {"evicted_ids": [], "active_count": 0, "max_active": max_active, "policy": eviction_policy}

    rows = await _fetch_generated_active_rows_for_capacity(user_id=uid)
    active_count = len(rows)
    if active_count <= int(max_active):
        return {
            "evicted_ids": [],
            "active_count": active_count,
            "max_active": int(max_active),
            "policy": eviction_policy,
        }

    evictable = [r for r in rows if not _row_locked(r)]
    if not evictable:
        logger.warning("capacity exceeded but no evictable generated reflections. user=%s active=%s max=%s", uid, active_count, max_active)
        return {
            "evicted_ids": [],
            "active_count": active_count,
            "max_active": int(max_active),
            "policy": eviction_policy,
            "warning": "no_evictable_rows",
        }

    policy = str(eviction_policy or "oldest").strip().lower()
    public_ids = [_row_public_id(r) for r in evictable if _row_public_id(r)]
    resonance_counts: Dict[str, int] = {}
    discovery_counts: Dict[str, int] = {}
    if policy == "low_resonance":
        resonance_counts = await _fetch_resonance_counts_by_public_ids(public_ids)
    elif policy == "low_discovery":
        discovery_counts = await _fetch_discovery_counts_by_public_ids(public_ids)

    def _sort_key(row: Dict[str, Any]) -> Tuple[Any, ...]:
        updated_at = str(row.get("updated_at") or row.get("created_at") or "")
        public_id = _row_public_id(row)
        if policy == "low_resonance":
            return (int(resonance_counts.get(public_id) or 0), updated_at)
        if policy == "low_discovery":
            return (int(discovery_counts.get(public_id) or 0), updated_at)
        return (updated_at,)

    evictable.sort(key=_sort_key)
    overflow = max(0, active_count - int(max_active))
    victims = evictable[:overflow]

    evicted_ids: List[str] = []
    for victim in victims:
        rid = _row_id(victim)
        if not rid:
            continue
        await _sb_patch_json(
            f"/rest/v1/{REFLECTIONS_TABLE}",
            params=[("id", f"eq.{rid}")],
            json_body={
                "status": "archived",
                "is_active": False,
                "published_at": None,
            },
            timeout=8.0,
            prefer="return=minimal",
        )
        evicted_ids.append(rid)

    return {
        "evicted_ids": evicted_ids,
        "active_count": active_count - len(evicted_ids),
        "max_active": int(max_active),
        "policy": policy,
    }


# ---------------------------------------------------------------------------
# misc helpers
# ---------------------------------------------------------------------------
def _unique_keep_order(values: Iterable[str]) -> List[str]:
    out: List[str] = []
    seen: Set[str] = set()
    for v in values:
        s = str(v or "").strip()
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out




async def retire_public_generated_reflections(*, user_id: str, limit: int = 1000) -> Dict[str, Any]:
    """Archive / deactivate currently public legacy generated reflections for one user.

    This helper is intentionally narrow and safe:
    - source_type = generated only
    - only rows that are still publicly visible (active or ready/published) are targeted
    - emotion_generated posts are untouched
    """
    uid = str(user_id or "").strip()
    if not uid:
        return {
            "user_id": "",
            "archived_ids": [],
            "archived_public_ids": [],
            "affected_count": 0,
        }

    rows = await _sb_get_json(
        f"/rest/v1/{REFLECTIONS_READ_TABLE}",
        params=[
            ("select", "id,public_id,status,is_active,updated_at,created_at"),
            ("owner_user_id", f"eq.{uid}"),
            ("source_type", "eq.generated"),
            ("order", "updated_at.desc,created_at.desc"),
            ("limit", str(max(1, int(limit)))),
        ],
        timeout=10.0,
    )

    target_rows = []
    for row in rows:
        status = str((row or {}).get("status") or "").strip().lower()
        is_active = bool((row or {}).get("is_active"))
        if is_active or status in {"ready", "published"}:
            target_rows.append(row)

    target_ids = [_row_id(row) for row in target_rows if _row_id(row)]
    if not target_ids:
        return {
            "user_id": uid,
            "archived_ids": [],
            "archived_public_ids": [],
            "affected_count": 0,
        }

    updated_rows = await _sb_patch_json(
        f"/rest/v1/{REFLECTIONS_TABLE}",
        params=[
            ("id", _quoted_in(target_ids)),
            ("owner_user_id", f"eq.{uid}"),
            ("source_type", "eq.generated"),
        ],
        json_body={
            "status": "archived",
            "is_active": False,
            "published_at": None,
        },
        timeout=10.0,
        prefer="return=representation",
    )

    archived_ids = [_row_id(row) for row in updated_rows if _row_id(row)]
    archived_public_ids = [_row_public_id(row) for row in updated_rows if _row_public_id(row)]
    return {
        "user_id": uid,
        "archived_ids": archived_ids,
        "archived_public_ids": archived_public_ids,
        "affected_count": len(archived_ids),
    }

__all__ = [
    "REFLECTIONS_READ_TABLE",
    "fetch_active_generated_reflections",
    "fetch_staged_generated_reflections",
    "fetch_lock_count",
    "stage_generation_plan",
    "promote_reflection",
    "reject_reflection",
    "fail_reflection",
    "enforce_capacity_policy",
    "retire_public_generated_reflections",
]
