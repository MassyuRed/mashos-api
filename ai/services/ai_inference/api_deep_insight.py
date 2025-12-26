# -*- coding: utf-8 -*-
"""api_deep_insight.py

Deep Insight API (FastAPI)

- GET  /deep_insight/questions
- POST /deep_insight/answers

v0.2 方針（Subscription対応）:
- tier はクライアント入力を信用せず、サーバー側で profiles.subscription_tier を参照して確定する。
- free は「1日1回」= 同日中は同じ質問バッチ（最大3問）を返す（再生成不可）。
  - フロント側のボタン制御だけに頼らず、APIレベルで破られないようにする。
- Deep Insight の回答は Supabase に保存し、MyProfile の推定に活用する。
- MyWeb（週報/月報）レポートには反映させない。
"""

from __future__ import annotations

import datetime as _dt
import logging
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI, Header, HTTPException, Query, Response
from pydantic import BaseModel, Field

from api_emotion_submit import _extract_bearer_token, _resolve_user_id_from_token
from astor_core import AstorEngine, AstorRequest, AstorMode
from astor_deep_insight import DeepInsightTemplateStore
from astor_deep_insight_question_store import DeepInsightServedStore
from astor_deep_insight_store import DeepInsightAnswerStore
from subscription import SubscriptionTier
from subscription_store import get_subscription_tier_for_user

logger = logging.getLogger("deep_insight_api")

astor_engine = AstorEngine()
answer_store = DeepInsightAnswerStore()
served_store = DeepInsightServedStore()

# 回答保存時の question_text 補完用 / キャッシュ返却時のテンプレ参照用
template_store = DeepInsightTemplateStore()


# ----------------------------
# Helpers
# ----------------------------


_JST = _dt.timezone(_dt.timedelta(hours=9))


def _parse_iso(ts: Any) -> Optional[_dt.datetime]:
    """Parse ISO8601-ish string to datetime (aware when possible)."""
    if not ts:
        return None
    s = str(ts).strip()
    if not s:
        return None
    try:
        # handle 'Z'
        s2 = s.replace("Z", "+00:00")
        return _dt.datetime.fromisoformat(s2)
    except Exception:
        return None


def _is_same_day_in_tz(ts: Any, tz: _dt.tzinfo) -> bool:
    d = _parse_iso(ts)
    if d is None:
        return False
    if d.tzinfo is None:
        # treat naive as UTC
        d = d.replace(tzinfo=_dt.timezone.utc)
    now = _dt.datetime.now(tz)
    return d.astimezone(tz).date() == now.date()


def _get_cached_batch_if_free(user_id: str) -> Tuple[bool, Optional[List[str]], Optional[str]]:
    """Return (hit, question_ids, generated_at) for free daily cache.

    Prefers JST day boundary. Falls back to store-provided helper when needed.
    """
    # v0.2 store: get_latest_batch_record() exists
    if hasattr(served_store, "get_latest_batch_record"):
        try:
            rec = served_store.get_latest_batch_record(user_id)
            if isinstance(rec, dict):
                qids = rec.get("question_ids") or []
                generated_at = rec.get("generated_at")
                if qids and _is_same_day_in_tz(generated_at, _JST):
                    return True, [str(x) for x in qids if str(x).strip()], str(generated_at or "")
        except Exception:
            pass

    # fallback: use helper method (may be UTC-based)
    if hasattr(served_store, "latest_batch_is_today_utc"):
        try:
            is_today, qids, generated_at = served_store.latest_batch_is_today_utc(user_id)  # type: ignore[attr-defined]
            if is_today and qids:
                return True, [str(x) for x in qids if str(x).strip()], str(generated_at or "")
        except Exception:
            pass

    return False, None, None


# ----------------------------
# Models
# ----------------------------


class DeepInsightQuestionItem(BaseModel):
    id: str
    text: str
    structure_key: Optional[str] = None
    hint: Optional[str] = None
    depth: int = 1
    strategy: str = "unexplored"


class DeepInsightQuestionsResponse(BaseModel):
    questions: List[DeepInsightQuestionItem]
    meta: Dict[str, Any] = {}


class DeepInsightAnswerItem(BaseModel):
    question_id: str = Field(..., description="Question id")
    structure_key: Optional[str] = Field(default=None, description="Structure key (optional)")
    text: str = Field(..., min_length=1, description="User answer")
    is_secret: bool = Field(default=True, description="If true, exclude from external MyProfile")


class DeepInsightAnswersRequest(BaseModel):
    answers: List[DeepInsightAnswerItem] = Field(..., description="List of answers")


class DeepInsightAnswersResponse(BaseModel):
    status: str
    saved: int
    meta: Dict[str, Any] = {}


# ----------------------------
# Route registration
# ----------------------------


def register_deep_insight_routes(app: FastAPI) -> None:
    """Register Deep Insight endpoints."""

    @app.get("/deep_insight/questions", response_model=DeepInsightQuestionsResponse)
    async def deep_insight_questions(
        response: Response,
        max_questions: int = Query(default=3, ge=1, le=5),
        max_depth: int = Query(default=1, ge=1, le=5),
        tier: str = Query(default="free"),  # 互換のため残す（サーバー側で上書き）
        lang: str = Query(default="ja"),
        context: Optional[str] = Query(default=None),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> DeepInsightQuestionsResponse:
        # Avoid proxy / client caching for question refresh
        try:
            if response is not None:
                response.headers["Cache-Control"] = "no-store"
                response.headers["Pragma"] = "no-cache"
        except Exception:
            pass

        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        user_id = await _resolve_user_id_from_token(access_token)

        # ✅ tier をサーバー側で確定（profiles.subscription_tier）
        try:
            tier_enum = await get_subscription_tier_for_user(user_id)
        except Exception as e:
            logger.warning("Failed to resolve subscription tier (fallback to FREE): %s", e)
            tier_enum = SubscriptionTier.FREE

        effective_tier = tier_enum.value

        # ✅ free: 同日中は同じバッチを返す（1日1回 = 再生成不可）
        if tier_enum == SubscriptionTier.FREE:
            hit, qids, generated_at = _get_cached_batch_if_free(user_id)
            if hit and qids:
                items: List[DeepInsightQuestionItem] = []
                for qid in qids[: max(1, int(max_questions))]:
                    tpl = template_store.find_by_id(qid) if qid else None
                    if not isinstance(tpl, dict):
                        continue

                    text = str(tpl.get("text") or "").strip()
                    if not text:
                        continue

                    hint = tpl.get("hint")
                    hint_s = str(hint).strip() if isinstance(hint, str) and hint.strip() else None
                    strategy = str(tpl.get("strategy") or "unexplored").strip() or "unexplored"

                    try:
                        items.append(
                            DeepInsightQuestionItem(
                                id=str(tpl.get("id") or qid),
                                text=text,
                                structure_key=(str(tpl.get("structure_key") or "").strip() or None),
                                hint=hint_s,
                                depth=int(tpl.get("depth") or 1),
                                strategy=strategy,
                            )
                        )
                    except Exception:
                        continue

                if items:
                    return DeepInsightQuestionsResponse(
                        questions=items,
                        meta={
                            "status": "ok",
                            "cached": True,
                            "cached_generated_at": generated_at,
                            "tier": effective_tier,
                            "can_regenerate": False,
                        },
                    )

        # 生成（free は「今日初回」だけ到達 / plus, premium は毎回生成できる）
        astor_req = AstorRequest(
            mode=AstorMode.DEEP_INSIGHT,
            user_id=user_id,
            options={
                "max_questions": max_questions,
                "max_depth": max_depth,
                "tier": effective_tier,  # ✅ server-asserted
                "lang": lang,
                "context": context,
            },
        )

        astor_resp = astor_engine.handle(astor_req)
        meta: Dict[str, Any] = dict(astor_resp.meta or {})
        raw_questions = meta.pop("questions", [])

        questions: List[DeepInsightQuestionItem] = []
        if isinstance(raw_questions, list):
            for q in raw_questions:
                if not isinstance(q, dict):
                    continue
                try:
                    questions.append(DeepInsightQuestionItem(**q))
                except Exception:
                    continue

        # フロントがUI制御に使える情報を付与
        meta["tier"] = effective_tier
        meta["cached"] = False
        meta["can_regenerate"] = (tier_enum != SubscriptionTier.FREE)

        return DeepInsightQuestionsResponse(questions=questions, meta=meta)

    @app.post("/deep_insight/answers", response_model=DeepInsightAnswersResponse)
    async def deep_insight_answers(
        body: DeepInsightAnswersRequest,
        response: Response,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> DeepInsightAnswersResponse:
        # Avoid proxy / client caching
        try:
            if response is not None:
                response.headers["Cache-Control"] = "no-store"
                response.headers["Pragma"] = "no-cache"
        except Exception:
            pass

        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        user_id = await _resolve_user_id_from_token(access_token)
        now_iso = _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

        packed: List[Dict[str, Any]] = []
        for a in body.answers:
            qid = (a.question_id or "").strip()
            tpl = template_store.find_by_id(qid) if qid else None

            packed.append(
                {
                    "question_id": qid,
                    "question_text": (str(tpl.get("text") or "").strip() if isinstance(tpl, dict) else None),
                    "structure_key": a.structure_key
                    or (str(tpl.get("structure_key") or "").strip() if isinstance(tpl, dict) else None),
                    "text": a.text,
                    "is_secret": bool(a.is_secret),
                    "created_at": now_iso,
                    "depth": int(tpl.get("depth") or 1) if isinstance(tpl, dict) else 1,
                    "strategy": (str(tpl.get("strategy") or "").strip() if isinstance(tpl, dict) else None),
                }
            )

        saved = answer_store.append_answers(user_id, packed)

        return DeepInsightAnswersResponse(
            status="ok",
            saved=int(saved),
            meta={
                "user_id": user_id,
                "saved_at": now_iso,
                "engine": "astor.deep_insight.answers.v0.2",
            },
        )
