# -*- coding: utf-8 -*-
"""api_mymodel_create.py

MyModel Create (template Q&A) API
--------------------------------

Provides:
  - GET  /mymodel/create/questions
  - POST /mymodel/create/answers

This is the "Create" entry screen for the new fixed-question Q&A architecture.

Key rules (2026-02)
  - Users may leave questions unanswered.
  - Create is considered "started" when at least one answer exists.
  - Answers are always readable.
  - Editing existing answers is Plus/Premium only.
    (New answers for previously-unanswered questions are allowed for any tier.)

Supabase tables (default names)
  - mymodel_create_questions
  - mymodel_create_answers

Notes
  - This API uses Supabase service_role to read/write via PostgREST.
  - RLS may be enabled; service_role bypasses it.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

import httpx
from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

from api_emotion_submit import (
    _ensure_supabase_config,
    _extract_bearer_token,
    _resolve_user_id_from_token,
)
from active_users_store import touch_active_user
from subscription import SubscriptionTier
from subscription_store import get_subscription_tier_for_user


logger = logging.getLogger("mymodel_create_api")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

QUESTIONS_TABLE = (os.getenv("COCOLON_MYMODEL_CREATE_QUESTIONS_TABLE", "mymodel_create_questions") or "").strip() or "mymodel_create_questions"
ANSWERS_TABLE = (os.getenv("COCOLON_MYMODEL_CREATE_ANSWERS_TABLE", "mymodel_create_answers") or "").strip() or "mymodel_create_answers"


# ----------------------------
# UI strings (server-managed)
# ----------------------------

PLACEHOLDER_DEFAULT = (os.getenv("COCOLON_MYMODEL_CREATE_PLACEHOLDER_DEFAULT", "一言でも大丈夫です") or "").strip() or "一言でも大丈夫です"
EDIT_LOCKED_MESSAGE = (os.getenv("COCOLON_MYMODEL_CREATE_EDIT_LOCKED_MESSAGE", "編集はPlus会員以上で利用できます") or "").strip() or "編集はPlus会員以上で利用できます"
CREATE_COMPLETED_MESSAGE = (os.getenv("COCOLON_MYMODEL_CREATE_COMPLETED_MESSAGE", "MyModelが作成されました") or "").strip() or "MyModelが作成されました"


def _ui_texts() -> Dict[str, str]:
    """UI-facing texts returned to RN (centralized on MashOS).

    RN should display these strings as-is.
    """
    return {
        "placeholder_default": PLACEHOLDER_DEFAULT,
        "edit_locked_message": EDIT_LOCKED_MESSAGE,
        "create_completed_message": CREATE_COMPLETED_MESSAGE,
    }


# ----------------------------
# Models
# ----------------------------


class MyModelCreateQuestionItem(BaseModel):
    question_id: int = Field(..., description="Template question id (1..)")
    question_text: str = Field(..., description="Question text")
    answer_text: Optional[str] = Field(default=None, description="Saved answer (if any)")
    answered: bool = Field(..., description="True if answered")
    updated_at: Optional[str] = Field(default=None, description="Answer updated_at (ISO)")
    is_secret: bool = Field(default=False, description="Secret flag for this answer (default false)")
    # Backward-compat: older clients may read `editable`.
    # RN should prefer `can_edit` and `edit_block_reason`.
    editable: bool = Field(..., description="True if the user can edit this answer (legacy field)")
    can_edit: bool = Field(..., description="True if the user can edit this answer")
    edit_block_reason: Optional[str] = Field(default=None, description="Reason why editing is blocked (if any)")
    placeholder: Optional[str] = Field(default=None, description="Placeholder text for the input")


class MyModelCreateQuestionsResponse(BaseModel):
    questions: List[MyModelCreateQuestionItem]
    meta: Dict[str, Any] = {}


class MyModelCreateAnswerItem(BaseModel):
    question_id: int = Field(..., description="Template question id")
    answer_text: Optional[str] = Field(default=None, description="Answer text. Empty/blank means 'clear'.")
    is_secret: Optional[bool] = Field(
        default=None,
        description="Secret flag (optional). If omitted, secret state is unchanged for existing answers.",
    )


class MyModelCreateAnswersRequest(BaseModel):
    answers: List[MyModelCreateAnswerItem] = Field(default_factory=list)


class MyModelCreateAnswersResponse(BaseModel):
    status: str = Field(..., description="ok | partial")
    saved: int = Field(..., description="Number of answers inserted/updated")
    deleted: int = Field(..., description="Number of answers deleted (cleared)")
    skipped_locked: int = Field(..., description="Skipped due to edit restriction")
    skipped_invalid: int = Field(..., description="Skipped due to invalid question id")
    skipped_empty: int = Field(..., description="Skipped because empty and nothing to clear")
    meta: Dict[str, Any] = {}


# ----------------------------
# Supabase helpers
# ----------------------------


def _sb_headers_json(*, prefer: Optional[str] = None) -> Dict[str, str]:
    _ensure_supabase_config()
    h = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


def _sb_headers(*, prefer: Optional[str] = None) -> Dict[str, str]:
    _ensure_supabase_config()
    h = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


async def _sb_get(path: str, *, params: Optional[Dict[str, str]] = None) -> httpx.Response:
    _ensure_supabase_config()
    url = f"{SUPABASE_URL}{path}"
    async with httpx.AsyncClient(timeout=8.0) as client:
        return await client.get(url, headers=_sb_headers(), params=params)


async def _sb_post(path: str, *, params: Optional[Dict[str, str]] = None, json: Any, prefer: Optional[str] = None) -> httpx.Response:
    _ensure_supabase_config()
    url = f"{SUPABASE_URL}{path}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        return await client.post(url, headers=_sb_headers_json(prefer=prefer), params=params, json=json)


async def _sb_delete(path: str, *, params: Dict[str, str]) -> httpx.Response:
    _ensure_supabase_config()
    url = f"{SUPABASE_URL}{path}"
    async with httpx.AsyncClient(timeout=8.0) as client:
        return await client.delete(url, headers=_sb_headers(), params=params)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


async def _fetch_questions(*, build_tier: str) -> List[Dict[str, Any]]:
    tier = (build_tier or "").strip().lower() or "light"
    # Questions are server-managed; filter by tier and is_active.
    resp = await _sb_get(
        f"/rest/v1/{QUESTIONS_TABLE}",
        params={
            "select": "id,question_text,sort_order,tier,is_active",
            "tier": f"eq.{tier}",
            "is_active": "eq.true",
            "order": "sort_order.asc",
        },
    )
    if resp.status_code >= 300:
        logger.error("Supabase %s select failed: %s %s", QUESTIONS_TABLE, resp.status_code, resp.text[:1500])
        raise HTTPException(status_code=502, detail="Failed to load create questions")
    rows = resp.json()
    return [r for r in rows if isinstance(r, dict)] if isinstance(rows, list) else []


async def _fetch_questions_all_active() -> List[Dict[str, Any]]:
    """Fetch all active questions across tiers.

    Notes:
    - We intentionally ignore build_tier here so the client can paginate/lock pages.
    - Ordering is server-managed by sort_order (then id for stability).
    """
    resp = await _sb_get(
        f"/rest/v1/{QUESTIONS_TABLE}",
        params={
            "select": "id,question_text,sort_order,tier,is_active",
            "is_active": "eq.true",
            "order": "sort_order.asc,id.asc",
        },
    )
    if resp.status_code >= 300:
        logger.error("Supabase %s select failed: %s %s", QUESTIONS_TABLE, resp.status_code, resp.text[:1500])
        raise HTTPException(status_code=502, detail="Failed to load create questions")
    rows = resp.json()
    return [r for r in rows if isinstance(r, dict)] if isinstance(rows, list) else []


async def _fetch_answers(*, user_id: str, question_ids: Optional[Set[int]] = None) -> Dict[int, Dict[str, Any]]:
    uid = str(user_id or "").strip()
    if not uid:
        return {}

    params: Dict[str, str] = {
        "select": "question_id,answer_text,updated_at,is_secret",
        "user_id": f"eq.{uid}",
    }
    # If filtering by question_ids, use `in.(...)`
    if question_ids:
        ids = sorted({int(x) for x in question_ids if isinstance(x, int) or str(x).strip().isdigit()})
        if ids:
            params["question_id"] = f"in.({','.join(str(i) for i in ids)})"

    resp = await _sb_get(f"/rest/v1/{ANSWERS_TABLE}", params=params)
    if resp.status_code >= 300:
        logger.error("Supabase %s select failed: %s %s", ANSWERS_TABLE, resp.status_code, resp.text[:1500])
        raise HTTPException(status_code=502, detail="Failed to load create answers")

    rows = resp.json()
    out: Dict[int, Dict[str, Any]] = {}
    if isinstance(rows, list):
        for r in rows:
            if not isinstance(r, dict):
                continue
            try:
                qid = int(r.get("question_id"))
            except Exception:
                continue
            out[qid] = r
    return out


def _is_paid_tier(tier: SubscriptionTier) -> bool:
    return tier in (SubscriptionTier.PLUS, SubscriptionTier.PREMIUM)


def register_mymodel_create_routes(app: FastAPI) -> None:
    @app.get("/mymodel/create/questions", response_model=MyModelCreateQuestionsResponse)
    async def mymodel_create_questions(
        build_tier: str = Query(default="light", description="Build tier (light|standard)."),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> MyModelCreateQuestionsResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        user_id = await _resolve_user_id_from_token(access_token)
        try:
            await touch_active_user(user_id, activity="mymodel_create_questions")
        except Exception as exc:
            logger.warning("Failed to touch active_users: %s", exc)

        tier_enum = await get_subscription_tier_for_user(user_id)
        paid = _is_paid_tier(tier_enum)

        # NOTE:
        # - For future: plus/premium may get standard (30) by default.
        # - For now, we honor the requested build_tier as long as questions exist.
        tier_norm = (build_tier or "").strip().lower() or "light"
        if tier_norm not in ("light", "standard"):
            tier_norm = "light"

                # Always return the full active question set across tiers (UI handles gating/pagination).
        questions = await _fetch_questions_all_active()
        qids: Set[int] = set()
        for q in questions:
            try:
                qids.add(int(q.get("id")))
            except Exception:
                continue

        answers = await _fetch_answers(user_id=user_id, question_ids=qids)

        items: List[MyModelCreateQuestionItem] = []
        answered_count = 0
        for q in questions:
            try:
                qid = int(q.get("id"))
            except Exception:
                continue
            qtext = str(q.get("question_text") or "").strip()
            ans = answers.get(qid)
            ans_text = (str(ans.get("answer_text") or "").strip() if isinstance(ans, dict) else "")
            ans_secret = (bool(ans.get("is_secret")) if isinstance(ans, dict) else False)
            is_answered = bool(ans_text)
            if is_answered:
                answered_count += 1

            # Editing existing answers is subscription-only.
            # Unanswered questions are always editable (so user can add new answers).
            editable = (paid if is_answered else True)
            updated_at = (str(ans.get("updated_at") or "").strip() if isinstance(ans, dict) else "") or None

            edit_block_reason = EDIT_LOCKED_MESSAGE if (is_answered and not paid) else None

            items.append(
                MyModelCreateQuestionItem(
                    question_id=qid,
                    question_text=qtext,
                    answer_text=(ans_text if is_answered else None),
                    answered=is_answered,
                    updated_at=updated_at,
                    is_secret=bool(ans_secret),
                    editable=bool(editable),
                    can_edit=bool(editable),
                    edit_block_reason=edit_block_reason,
                    placeholder=PLACEHOLDER_DEFAULT,
                )
            )

        total = len(items)
        has_unanswered = (answered_count < total) if total > 0 else True
        is_created = answered_count > 0

        return MyModelCreateQuestionsResponse(
            questions=items,
            meta={
                "user_id": user_id,
                "build_tier": tier_norm,
                "subscription_tier": tier_enum.value,
                "can_edit_existing": bool(paid),  # legacy
                "can_edit_answers": bool(paid),
                "total_questions": int(total),
                "answered_count": int(answered_count),
                "unanswered_count": int(max(0, total - answered_count)),
                "has_unanswered": bool(has_unanswered),
                "is_created": bool(is_created),
                "show_incomplete_badge": bool(has_unanswered),
                "incomplete_badge_count": int(max(0, total - answered_count)),
                "engine": "mymodel.create.questions.v1",
                "ui_texts": _ui_texts(),
            },
        )

    @app.post("/mymodel/create/answers", response_model=MyModelCreateAnswersResponse)
    async def mymodel_create_answers(
        body: MyModelCreateAnswersRequest,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> MyModelCreateAnswersResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        user_id = await _resolve_user_id_from_token(access_token)
        try:
            await touch_active_user(user_id, activity="mymodel_create_answers")
        except Exception as exc:
            logger.warning("Failed to touch active_users: %s", exc)

        tier_enum = await get_subscription_tier_for_user(user_id)
        paid = _is_paid_tier(tier_enum)

        # Load allowed question ids (light only for now).
        # If/when standard is introduced, the client can either:
        #  - call GET /mymodel/create/questions?build_tier=standard, then POST answers accordingly
        #  - or keep using light.
        # Here we accept any question_id that exists in questions table (any tier), to keep the API flexible.
        # But we still validate ids against the DB.
        raw_ids: Set[int] = set()
        for a in (body.answers or []):
            try:
                raw_ids.add(int(a.question_id))
            except Exception:
                continue

        # Fetch questions for both tiers to validate ids (best-effort).
        # (Keeps client simple and prevents writing arbitrary question_id.)
        allowed_ids: Set[int] = set()
        try:
            for tier_name in ("light", "standard"):
                qs = await _fetch_questions(build_tier=tier_name)
                for q in qs:
                    try:
                        allowed_ids.add(int(q.get("id")))
                    except Exception:
                        continue
        except Exception:
            # If questions load fails, surface as 502.
            raise

        valid_ids = {qid for qid in raw_ids if qid in allowed_ids}
        existing = await _fetch_answers(user_id=user_id, question_ids=valid_ids)

        saved_payload: List[Dict[str, Any]] = []
        delete_ids: Set[int] = set()
        skipped_locked_ids: Set[int] = set()
        skipped_invalid_ids: Set[int] = set()
        skipped_empty_ids: Set[int] = set()

        now_iso = _now_iso()

        for a in (body.answers or []):
            try:
                qid = int(a.question_id)
            except Exception:
                continue

            if qid not in allowed_ids:
                skipped_invalid_ids.add(qid)
                continue

            new_text = str(a.answer_text or "")
            # normalize: trim whitespace but keep internal newlines
            new_text_stripped = new_text.strip()

            prev = existing.get(qid)
            prev_text = (str(prev.get("answer_text") or "").strip() if isinstance(prev, dict) else "")
            prev_secret = (bool(prev.get("is_secret")) if isinstance(prev, dict) else False)
            has_prev = bool(prev_text)

            # is_secret is optional for backward compatibility.
            # - If omitted on existing answers, keep current secret flag.
            # - If omitted on new answers, default to False.
            new_secret_opt = getattr(a, "is_secret", None)
            desired_secret = (
                prev_secret
                if (new_secret_opt is None and has_prev)
                else (bool(new_secret_opt) if new_secret_opt is not None else False)
            )

            # Empty/blank => clear
            if not new_text_stripped:
                if not has_prev:
                    skipped_empty_ids.add(qid)
                    continue
                if not paid:
                    skipped_locked_ids.add(qid)
                    continue
                delete_ids.add(qid)
                continue

            # If already answered, editing text is subscription-only.
            if has_prev and not paid:
                # Allow secret-only updates when text is unchanged.
                if new_text_stripped == prev_text:
                    if (new_secret_opt is not None) and (desired_secret != prev_secret):
                        saved_payload.append(
                            {
                                "user_id": user_id,
                                "question_id": qid,
                                "is_secret": bool(desired_secret),
                            }
                        )
                    continue
                # Allow no-op if the text is unchanged.
                skipped_locked_ids.add(qid)
                continue

            # Upsert row
            row: Dict[str, Any] = {
                "user_id": user_id,
                "question_id": qid,
                "answer_text": new_text_stripped,
                "is_secret": bool(desired_secret),
                "updated_at": now_iso,
            }

            # If only secret changed (text unchanged), do not bump updated_at.
            if has_prev and new_text_stripped == prev_text and desired_secret != prev_secret:
                row.pop("updated_at", None)
                row.pop("answer_text", None)

            saved_payload.append(row)

        # Apply deletes first (so clearing + re-saving in same batch behaves deterministically).
        deleted = 0
        if delete_ids:
            # PostgREST: DELETE with multiple ids
            # Example: question_id=in.(1,2,3)&user_id=eq.<uid>
            ids_csv = ",".join(str(i) for i in sorted(delete_ids))
            resp_del = await _sb_delete(
                f"/rest/v1/{ANSWERS_TABLE}",
                params={
                    "user_id": f"eq.{user_id}",
                    "question_id": f"in.({ids_csv})",
                },
            )
            if resp_del.status_code not in (200, 202, 204):
                logger.error("Supabase %s delete failed: %s %s", ANSWERS_TABLE, resp_del.status_code, resp_del.text[:1500])
                raise HTTPException(status_code=502, detail="Failed to clear create answers")
            deleted = len(delete_ids)

        saved = 0
        if saved_payload:
            # Upsert by (user_id,question_id)
            resp = await _sb_post(
                f"/rest/v1/{ANSWERS_TABLE}",
                params={"on_conflict": "user_id,question_id"},
                json=saved_payload,
                prefer="resolution=merge-duplicates,return=minimal",
            )
            if resp.status_code not in (200, 201, 204):
                logger.error("Supabase %s upsert failed: %s %s", ANSWERS_TABLE, resp.status_code, resp.text[:1500])
                raise HTTPException(status_code=502, detail="Failed to save create answers")
            saved = len(saved_payload)

        skipped_locked = len(skipped_locked_ids)
        skipped_invalid = len(skipped_invalid_ids)
        skipped_empty = len(skipped_empty_ids)

        status = "ok" if (skipped_locked + skipped_invalid) == 0 else "partial"

        # Optional: return updated create-state so RN can update badge without an extra GET.
        create_state: Optional[Dict[str, Any]] = None
        try:
            qs_light = await _fetch_questions(build_tier="light")
            qids_light: Set[int] = set()
            for q in qs_light:
                try:
                    qids_light.add(int(q.get("id")))
                except Exception:
                    continue
            ans_light = await _fetch_answers(user_id=user_id, question_ids=qids_light)
            answered_light = 0
            for _, row in (ans_light or {}).items():
                if isinstance(row, dict) and str(row.get("answer_text") or "").strip():
                    answered_light += 1
            total_light = len(qids_light)
            has_unanswered_light = (answered_light < total_light) if total_light > 0 else True
            create_state = {
                "build_tier": "light",
                "total_questions": int(total_light),
                "answered_count": int(answered_light),
                "unanswered_count": int(max(0, total_light - answered_light)),
                "has_unanswered": bool(has_unanswered_light),
                "is_created": bool(answered_light > 0),
                "show_incomplete_badge": bool(has_unanswered_light),
                "incomplete_badge_count": int(max(0, total_light - answered_light)),
            }
        except Exception as exc:
            logger.warning("Failed to compute create_state: %s", exc)
            create_state = None

        locked_items = [
            {"question_id": int(qid), "reason": EDIT_LOCKED_MESSAGE}
            for qid in sorted(skipped_locked_ids)
        ]
        invalid_items = [
            {"question_id": int(qid), "reason": "無効な質問IDです"}
            for qid in sorted(skipped_invalid_ids)
        ]

        return MyModelCreateAnswersResponse(
            status=status,
            saved=int(saved),
            deleted=int(deleted),
            skipped_locked=int(skipped_locked),
            skipped_invalid=int(skipped_invalid),
            skipped_empty=int(skipped_empty),
            meta={
                "user_id": user_id,
                "subscription_tier": tier_enum.value,
                "can_edit_existing": bool(paid),  # legacy
                "can_edit_answers": bool(paid),
                "saved_at": now_iso,
                "engine": "mymodel.create.answers.v1",
                # Optional: expose which ids were blocked (helps client debug)
                "locked_question_ids": sorted(skipped_locked_ids),
                "invalid_question_ids": sorted(skipped_invalid_ids),
                "locked": locked_items,
                "invalid": invalid_items,
                "create_state": create_state,
                "ui_texts": _ui_texts(),
            },
        )
