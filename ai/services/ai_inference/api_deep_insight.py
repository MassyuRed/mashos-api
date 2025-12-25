# -*- coding: utf-8 -*-
"""api_deep_insight.py

Deep Insight API (FastAPI)

- GET  /deep_insight/questions
- POST /deep_insight/answers

v0.1 方針:
- 「ASTORに構造を作って、画面と出力を作る」ための最小スケルトン。
- 問いの構文・保存の構造だけ先に作り、実際の問い生成（文言）は後から調整できるようにする。

重要:
- Deep Insight で得た回答は **MyProfileの分析情報として活用**する。
- MyWeb（週報/月報）レポートには反映させない。
"""

from __future__ import annotations

import datetime as _dt
import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException, Query, Response
from pydantic import BaseModel, Field

from api_emotion_submit import _extract_bearer_token, _resolve_user_id_from_token
from astor_core import AstorEngine, AstorRequest, AstorMode
from astor_deep_insight import DeepInsightTemplateStore
from astor_deep_insight_store import DeepInsightAnswerStore

logger = logging.getLogger("deep_insight_api")

astor_engine = AstorEngine()
answer_store = DeepInsightAnswerStore()
# 回答保存時の question_text 補完用
template_store = DeepInsightTemplateStore()


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
        tier: str = Query(default="free"),
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

        astor_req = AstorRequest(
            mode=AstorMode.DEEP_INSIGHT,
            user_id=user_id,
            options={
                "max_questions": max_questions,
                "max_depth": max_depth,
                "tier": tier,
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

        return DeepInsightQuestionsResponse(questions=questions, meta=meta)

    @app.post("/deep_insight/answers", response_model=DeepInsightAnswersResponse)
    async def deep_insight_answers(
        body: DeepInsightAnswersRequest,
        response: Response,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> DeepInsightAnswersResponse:
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
                "engine": "astor.deep_insight.answers.v0.1",
            },
        )
