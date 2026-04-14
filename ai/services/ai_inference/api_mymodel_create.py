# -*- coding: utf-8 -*-
"""api_mymodel_create.py

MyModel Create (template Q&A) API
--------------------------------

Provides:
  - GET  /mymodel/create/questions
  - POST /mymodel/create/answers

This is the "Create" entry screen for the new fixed-question Q&A architecture.

Key rules (2026-04)
  - ProfileCreate uses the fixed free question set only (5 questions).
  - Users may leave questions unanswered.
  - Answers are always readable by the owner.
  - Editing existing answers is allowed for all plans.
  - Secret answers remain hidden from other users on Account.

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

# Shared Supabase HTTP client (connection pooled)
from supabase_client import (
    sb_delete as _sb_delete_shared,
    sb_get as _sb_get_shared,
    sb_post as _sb_post_shared,
    sb_service_role_headers as _sb_headers_shared,
    sb_service_role_headers_json as _sb_headers_json_shared,
)
from active_users_store import touch_active_user
from subscription import SubscriptionTier
from subscription_store import get_subscription_tier_for_user
from astor_snapshot_enqueue import enqueue_global_snapshot_refresh
from astor_account_status_enqueue import enqueue_account_status_refresh
from mymodel_entitlements import (
    FREE_TEMPLATE_QUESTION_LIMIT,
    LIGHT_BUILD_TIER,
    filter_question_rows_for_build_tier,
    resolve_mymodel_entitlement,
)
from reflection_text_formatter import (
    REFLECTION_DISPLAY_VERSION,
    apply_reflection_storage_fields,
)


logger = logging.getLogger("mymodel_create_api")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

QUESTIONS_TABLE = (os.getenv("COCOLON_MYMODEL_CREATE_QUESTIONS_TABLE", "mymodel_create_questions") or "").strip() or "mymodel_create_questions"
ANSWERS_TABLE = (os.getenv("COCOLON_MYMODEL_CREATE_ANSWERS_TABLE", "mymodel_create_answers") or "").strip() or "mymodel_create_answers"


# ----------------------------
# UI strings (server-managed)
# ----------------------------

PLACEHOLDER_DEFAULT = (os.getenv("COCOLON_MYMODEL_CREATE_PLACEHOLDER_DEFAULT", "ここに書いてください。") or "").strip() or "ここに書いてください。"
EDIT_LOCKED_MESSAGE = (os.getenv("COCOLON_MYMODEL_CREATE_EDIT_LOCKED_MESSAGE", "") or "").strip()
CREATE_COMPLETED_MESSAGE = (os.getenv("COCOLON_MYMODEL_CREATE_COMPLETED_MESSAGE", "ProfileCreateを保存しました") or "").strip() or "ProfileCreateを保存しました"
INTRO_SUBSCRIPTION_BENEFIT = (
    os.getenv(
        "COCOLON_MYMODEL_CREATE_INTRO_SUBSCRIPTION_BENEFIT",
        "ProfileCreate は固定的な自己紹介 / プロフィール資産です。",
    )
    or ""
).strip() or "ProfileCreate は固定的な自己紹介 / プロフィール資産です。"
INTRO_SECRET_TOGGLE_NOTE = (
    os.getenv(
        "COCOLON_MYMODEL_CREATE_INTRO_SECRET_TOGGLE_NOTE",
        "シークレットメモをオンにすると、他ユーザーの Account には表示されません。",
    )
    or ""
).strip() or "シークレットメモをオンにすると、他ユーザーの Account には表示されません。"
FREE_ACCESSIBLE_QUESTION_COUNT = int(FREE_TEMPLATE_QUESTION_LIMIT)

ANSWER_SELECT_BASE = "question_id,answer_text,updated_at,is_secret"
ANSWER_SELECT_WITH_DISPLAY = "question_id,answer_text,updated_at,is_secret,reflection_display_text,reflection_display_state,reflection_format_version,reflection_format_meta,reflection_display_updated_at"
REFLECTION_DISPLAY_STORAGE_FIELDS = frozenset({
    "reflection_display_text",
    "reflection_display_state",
    "reflection_format_version",
    "reflection_format_meta",
    "reflection_display_updated_at",
})


def _looks_like_missing_reflection_display_columns(detail: Any) -> bool:
    txt = str(detail or "").lower()
    return ("reflection_display_" in txt) or ("reflection_format_" in txt)


def _strip_reflection_display_columns(row: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(row, dict):
        return {}
    return {k: v for k, v in row.items() if k not in REFLECTION_DISPLAY_STORAGE_FIELDS}


def _ui_texts() -> Dict[str, str]:
    """UI-facing texts returned to RN (centralized on MashOS).

    RN should display these strings as-is.
    """
    return {
        "placeholder_default": PLACEHOLDER_DEFAULT,
        "edit_locked_message": EDIT_LOCKED_MESSAGE,
        "create_completed_message": CREATE_COMPLETED_MESSAGE,
        "intro_subscription_benefit": INTRO_SUBSCRIPTION_BENEFIT,
        "intro_secret_toggle_note": INTRO_SECRET_TOGGLE_NOTE,
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


class AccountProfileCreateItem(BaseModel):
    question_id: int = Field(..., description="Template question id")
    question_text: str = Field(..., description="Question text")
    answer_text: str = Field(..., description="Answer text for Account display")
    updated_at: Optional[str] = Field(default=None, description="Answer updated_at (ISO)")
    is_secret: bool = Field(default=False, description="Secret flag for this answer")


class AccountProfileCreateResponse(BaseModel):
    items: List[AccountProfileCreateItem]
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
    return _sb_headers_json_shared(prefer=prefer)


def _sb_headers(*, prefer: Optional[str] = None) -> Dict[str, str]:
    return _sb_headers_shared(prefer=prefer)


async def _sb_get(path: str, *, params: Optional[Dict[str, str]] = None) -> httpx.Response:
    return await _sb_get_shared(path, params=params, headers=_sb_headers(), timeout=8.0)


async def _sb_post(path: str, *, params: Optional[Dict[str, str]] = None, json: Any, prefer: Optional[str] = None) -> httpx.Response:
    return await _sb_post_shared(path, params=params, json=json, prefer=prefer, timeout=10.0)


async def _sb_delete(path: str, *, params: Dict[str, str]) -> httpx.Response:
    return await _sb_delete_shared(path, params=params, headers=_sb_headers(), timeout=8.0)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


async def _fetch_questions(*, build_tier: str) -> List[Dict[str, Any]]:
    rows = await _fetch_questions_all_active()
    return filter_question_rows_for_build_tier(rows, build_tier=build_tier)


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

    base_params: Dict[str, str] = {
        "user_id": f"eq.{uid}",
    }
    # If filtering by question_ids, use `in.(...)`
    if question_ids:
        ids = sorted({int(x) for x in question_ids if isinstance(x, int) or str(x).strip().isdigit()})
        if ids:
            base_params["question_id"] = f"in.({','.join(str(i) for i in ids)})"

    params_v2 = dict(base_params)
    params_v2["select"] = ANSWER_SELECT_WITH_DISPLAY
    resp = await _sb_get(f"/rest/v1/{ANSWERS_TABLE}", params=params_v2)
    if resp.status_code >= 300 and _looks_like_missing_reflection_display_columns(resp.text):
        logger.warning("Reflection display columns not available on %s yet; falling back to base select", ANSWERS_TABLE)
        params_v1 = dict(base_params)
        params_v1["select"] = ANSWER_SELECT_BASE
        resp = await _sb_get(f"/rest/v1/{ANSWERS_TABLE}", params=params_v1)

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


def _can_edit_answer_text(*, entitlement: Any, is_answered: bool) -> bool:
    if not is_answered:
        return True
    return bool(getattr(entitlement, "can_edit_existing_answers", False))


def _resolve_account_profile_answer_text(*, answer_row: Optional[Dict[str, Any]], is_self: bool) -> Optional[str]:
    if not isinstance(answer_row, dict):
        return None

    raw_text = str(answer_row.get("answer_text") or "").strip()
    if not raw_text:
        return None

    if is_self:
        return raw_text

    if bool(answer_row.get("is_secret")):
        return None

    display_state = str(answer_row.get("reflection_display_state") or "").strip().lower()
    if display_state == "blocked":
        return None

    display_text = str(answer_row.get("reflection_display_text") or raw_text).strip()
    return display_text or None


def _build_account_profile_items(*, questions: List[Dict[str, Any]], answers: Dict[int, Dict[str, Any]], is_self: bool) -> Tuple[List[AccountProfileCreateItem], int]:
    items: List[AccountProfileCreateItem] = []
    answered_count = 0

    for q in questions:
        try:
            qid = int(q.get("id"))
        except Exception:
            continue
        question_text = str(q.get("question_text") or "").strip()
        answer_row = answers.get(qid)
        raw_answer_text = str((answer_row or {}).get("answer_text") or "").strip()
        if raw_answer_text:
            answered_count += 1

        account_answer_text = _resolve_account_profile_answer_text(answer_row=answer_row, is_self=is_self)
        if not account_answer_text:
            continue

        items.append(
            AccountProfileCreateItem(
                question_id=qid,
                question_text=question_text,
                answer_text=account_answer_text,
                updated_at=(str((answer_row or {}).get("updated_at") or "").strip() or None),
                is_secret=bool((answer_row or {}).get("is_secret") or False),
            )
        )

    return items, answered_count


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
        entitlement = resolve_mymodel_entitlement(tier_enum)
        effective_build_tier = LIGHT_BUILD_TIER

        questions = await _fetch_questions(build_tier=effective_build_tier)
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

            editable = _can_edit_answer_text(entitlement=entitlement, is_answered=is_answered)
            updated_at = (str(ans.get("updated_at") or "").strip() if isinstance(ans, dict) else "") or None
            edit_block_reason = None if editable else EDIT_LOCKED_MESSAGE

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
                "build_tier": effective_build_tier,
                "subscription_tier": tier_enum.value,
                "can_edit_existing": bool(entitlement.can_edit_existing_answers),
                "can_edit_answers": True,
                "can_toggle_secret_without_edit": True,
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

    @app.get("/account/profile-create", response_model=AccountProfileCreateResponse)
    async def account_profile_create(
        target_user_id: Optional[str] = Query(default=None, description="Target user id for Account display."),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> AccountProfileCreateResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        viewer_user_id = await _resolve_user_id_from_token(access_token)
        resolved_target_user_id = str(target_user_id or viewer_user_id or "").strip() or str(viewer_user_id)
        is_self = resolved_target_user_id == str(viewer_user_id)

        try:
            await touch_active_user(viewer_user_id, activity="account_profile_create")
        except Exception as exc:
            logger.warning("Failed to touch active_users: %s", exc)

        questions = await _fetch_questions(build_tier=LIGHT_BUILD_TIER)
        question_ids: Set[int] = set()
        for q in questions:
            try:
                question_ids.add(int(q.get("id")))
            except Exception:
                continue

        answers = await _fetch_answers(user_id=resolved_target_user_id, question_ids=question_ids)
        items, answered_count = _build_account_profile_items(
            questions=questions,
            answers=answers,
            is_self=is_self,
        )

        return AccountProfileCreateResponse(
            items=items,
            meta={
                "viewer_user_id": viewer_user_id,
                "target_user_id": resolved_target_user_id,
                "is_self": bool(is_self),
                "total_questions": int(len(question_ids)),
                "answered_count": int(answered_count),
                "visible_answered_count": int(len(items)),
                "can_edit": bool(is_self),
                "label": "ProfileCreate",
                "engine": "account.profile_create.v1",
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
        entitlement = resolve_mymodel_entitlement(tier_enum)
        effective_build_tier = LIGHT_BUILD_TIER

        raw_ids: Set[int] = set()
        for a in (body.answers or []):
            try:
                raw_ids.add(int(a.question_id))
            except Exception:
                continue

        all_active_questions = await _fetch_questions_all_active()
        all_active_ids: Set[int] = set()
        for q in all_active_questions:
            try:
                all_active_ids.add(int(q.get("id")))
            except Exception:
                continue

        visible_questions = filter_question_rows_for_build_tier(
            all_active_questions,
            build_tier=effective_build_tier,
        )
        can_edit_existing_answers = bool(entitlement.can_edit_existing_answers)
        allowed_ids: Set[int] = set()
        for q in visible_questions:
            try:
                allowed_ids.add(int(q.get("id")))
            except Exception:
                continue

        valid_ids = {qid for qid in raw_ids if qid in allowed_ids}
        existing = await _fetch_answers(user_id=user_id, question_ids=valid_ids)

        saved_payload: List[Dict[str, Any]] = []
        delete_ids: Set[int] = set()
        skipped_locked_ids: Set[int] = set()
        skipped_invalid_ids: Set[int] = set()
        skipped_empty_ids: Set[int] = set()
        formatting_changed_ids: Set[int] = set()
        formatting_masked_ids: Set[int] = set()
        formatting_blocked_ids: Set[int] = set()

        now_iso = _now_iso()

        def _build_formatted_row(*, qid: int, row: Dict[str, Any], raw_text: str, display_updated_at: Optional[str]) -> Dict[str, Any]:
            formatted_row, display_result = apply_reflection_storage_fields(
                row,
                raw_text=raw_text,
                display_updated_at=display_updated_at,
            )
            if bool(display_result.changed):
                formatting_changed_ids.add(int(qid))
            if str(display_result.display_state) == "masked":
                formatting_masked_ids.add(int(qid))
            elif str(display_result.display_state) == "blocked":
                formatting_blocked_ids.add(int(qid))
            return formatted_row

        for a in (body.answers or []):
            try:
                qid = int(a.question_id)
            except Exception:
                continue

            if qid not in all_active_ids:
                skipped_invalid_ids.add(qid)
                continue
            if qid not in allowed_ids:
                skipped_locked_ids.add(qid)
                continue

            prev = existing.get(qid)
            prev_text = (str(prev.get("answer_text") or "").strip() if isinstance(prev, dict) else "")
            prev_secret = (bool(prev.get("is_secret")) if isinstance(prev, dict) else False)
            has_prev = bool(prev_text)

            has_answer_text = getattr(a, "answer_text", None) is not None
            new_text_stripped: Optional[str] = None
            if has_answer_text:
                new_text = str(a.answer_text or "")
                # normalize: trim whitespace but keep internal newlines
                new_text_stripped = new_text.strip()

            # is_secret is optional for backward compatibility.
            # - If omitted on existing answers, keep current secret flag.
            # - If omitted on new answers, default to False.
            new_secret_opt = getattr(a, "is_secret", None)
            desired_secret = (
                prev_secret
                if (new_secret_opt is None and has_prev)
                else (bool(new_secret_opt) if new_secret_opt is not None else False)
            )

            if has_prev and not can_edit_existing_answers:
                if has_answer_text and new_text_stripped != prev_text:
                    skipped_locked_ids.add(qid)
                    continue
                if desired_secret == prev_secret:
                    continue
                saved_payload.append(
                    _build_formatted_row(
                        qid=qid,
                        row={
                            "user_id": user_id,
                            "question_id": qid,
                            "answer_text": prev_text,
                            "is_secret": bool(desired_secret),
                        },
                        raw_text=prev_text,
                        display_updated_at=now_iso,
                    )
                )
                continue

            if has_prev and not has_answer_text:
                if desired_secret == prev_secret:
                    continue
                saved_payload.append(
                    _build_formatted_row(
                        qid=qid,
                        row={
                            "user_id": user_id,
                            "question_id": qid,
                            "answer_text": prev_text,
                            "is_secret": bool(desired_secret),
                        },
                        raw_text=prev_text,
                        display_updated_at=now_iso,
                    )
                )
                continue

            # Empty/blank => clear
            if not new_text_stripped:
                if not has_prev:
                    skipped_empty_ids.add(qid)
                    continue
                delete_ids.add(qid)
                continue

            if has_prev and new_text_stripped == prev_text and desired_secret == prev_secret:
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

            saved_payload.append(
                _build_formatted_row(
                    qid=qid,
                    row=row,
                    raw_text=str(new_text_stripped or ""),
                    display_updated_at=now_iso,
                )
            )

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
            if resp.status_code not in (200, 201, 204) and _looks_like_missing_reflection_display_columns(resp.text):
                logger.warning("Reflection display columns not available on %s yet; retrying save without display fields", ANSWERS_TABLE)
                fallback_payload = [_strip_reflection_display_columns(row) for row in saved_payload]
                resp = await _sb_post(
                    f"/rest/v1/{ANSWERS_TABLE}",
                    params={"on_conflict": "user_id,question_id"},
                    json=fallback_payload,
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
            accessible_qids: Set[int] = set()
            for q in visible_questions:
                try:
                    accessible_qids.add(int(q.get("id")))
                except Exception:
                    continue
            ans_accessible = await _fetch_answers(user_id=user_id, question_ids=accessible_qids)
            answered_accessible = 0
            for _, row in (ans_accessible or {}).items():
                if isinstance(row, dict) and str(row.get("answer_text") or "").strip():
                    answered_accessible += 1
            total_accessible = len(accessible_qids)
            has_unanswered_accessible = (
                (answered_accessible < total_accessible) if total_accessible > 0 else True
            )
            create_state = {
                "build_tier": effective_build_tier,
                "total_questions": int(total_accessible),
                "answered_count": int(answered_accessible),
                "unanswered_count": int(max(0, total_accessible - answered_accessible)),
                "has_unanswered": bool(has_unanswered_accessible),
                "is_created": bool(answered_accessible > 0),
                "show_incomplete_badge": bool(has_unanswered_accessible),
                "incomplete_badge_count": int(max(0, total_accessible - answered_accessible)),
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

        if int(saved or 0) > 0 or int(deleted or 0) > 0:
            try:
                await enqueue_global_snapshot_refresh(
                    user_id=user_id,
                    trigger="mymodel_create_answers",
                    requested_at=now_iso,
                    debounce=True,
                )
            except Exception as exc:
                logger.warning("snapshot enqueue failed (mymodel_create_answers): %s", exc)

            try:
                await enqueue_account_status_refresh(
                    target_user_id=user_id,
                    trigger="mymodel_create_answers",
                    requested_at=now_iso,
                    debounce=True,
                )
            except Exception as exc:
                logger.warning("account status enqueue failed (mymodel_create_answers): %s", exc)

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
                "can_edit_existing": bool(entitlement.can_edit_existing_answers),
                "can_edit_answers": True,
                "can_toggle_secret_without_edit": True,
                "saved_at": now_iso,
                "engine": "mymodel.create.answers.v1",
                # Optional: expose which ids were blocked (helps client debug)
                "locked_question_ids": sorted(skipped_locked_ids),
                "invalid_question_ids": sorted(skipped_invalid_ids),
                "locked": locked_items,
                "invalid": invalid_items,
                "create_state": create_state,
                "reflection_formatting": {
                    "version": REFLECTION_DISPLAY_VERSION,
                    "changed_question_ids": sorted(formatting_changed_ids),
                    "masked_question_ids": sorted(formatting_masked_ids),
                    "blocked_question_ids": sorted(formatting_blocked_ids),
                    "changed_count": int(len(formatting_changed_ids)),
                    "masked_count": int(len(formatting_masked_ids)),
                    "blocked_count": int(len(formatting_blocked_ids)),
                },
                "ui_texts": _ui_texts(),
            },
        )
