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
import os
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI, Header, HTTPException, Query, Response
from pydantic import BaseModel, Field

from api_emotion_submit import _extract_bearer_token, _resolve_user_id_from_token
from active_users_store import touch_active_user
from astor_core import AstorEngine, AstorRequest, AstorMode
from astor_deep_insight import DeepInsightTemplateStore
from astor_deep_insight_question_store import DeepInsightServedStore
from astor_deep_insight_store import DeepInsightAnswerStore
from subscription import SubscriptionTier
from subscription_store import get_subscription_tier_for_user
from ui_text_templates import render_deep_insight_question_text
from deep_insight_strategy import build_deep_insight_strategy_config

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




def _build_ui_config(tier: SubscriptionTier, lang: str = "ja") -> Dict[str, Any]:
    """Return UI config (limits / strings / display rules) for Deep Insight.

    Phase5.2:
    - JS側の固定文や制御値を減らし、MashOS側で一元管理できるようにする。
    - 互換性のため、クライアントが古くても動くよう meta に付与するだけ（必須にはしない）。
    """
    lang_norm = (lang or "ja").strip().lower()
    if lang_norm not in ("ja", "en"):
        lang_norm = "ja"

    # 今は既存挙動を変えない（将来ここを変えるだけで全端末へ反映できる）
    max_questions = 3
    max_depth = 1

    # tier によって今後拡張可能（例：plus/premium で上限UPなど）
    # 現段階では安全に現状維持
    if tier == SubscriptionTier.PREMIUM:
        max_questions = 3
        max_depth = 1
    elif tier == SubscriptionTier.PLUS:
        max_questions = 3
        max_depth = 1

    if lang_norm == "en":
        strings: Dict[str, str] = {
            "panel_title": "Deep Insight",
            "back_label": "MyWeb",
            "intro_title": "Generate questions and reflect them in your self-structure analysis.",
            "intro_text": "These questions help understand your structure a bit deeper. You can leave any you don't want to answer blank.",
            "answer_placeholder": "Write here.",
            "submit_button": "Send",
            "cancel_button": "Not now",
            "regenerate_button": "Get another set",
            "empty_text": "No questions available right now.",
            "secret_on": "Secret",
            "secret_off": "Public",
            "paywall_title": "Generating another set is limited",
            "paywall_text": "With your current plan, you cannot get another set. Upgrade to Plus to generate questions anytime.",
            "paywall_button": "Upgrade to Plus",
            "paywall_alert_title": "Plus required",
            "paywall_alert_text": "With your current plan, you cannot get another set.\n\nPlease check your plan from the Account screen.",
            "footer_text": "* Deep Insight answers are used for MyProfile analysis. They are not reflected in MyWeb reports.",
        }
    else:
        strings = {
            "panel_title": "Deep Insight",
            "back_label": "MyWeb",
            "intro_title": "問いを生成し、自己構造分析に反映します。",
            "intro_text": "いまのあなたの構造をもう少し深く理解するための問いです。答えたくないものは空欄のままで大丈夫です。",
            "answer_placeholder": "ここに書いてください。",
            "submit_button": "送る",
            "cancel_button": "今はやめておく",
            "regenerate_button": "別の問いを受け取る",
            "empty_text": "いまは質問がありません。",
            "secret_on": "シークレット",
            "secret_off": "公開",
            "paywall_title": "次の問いの生成は制限されています",
            "paywall_text": "現在のプランでは「別の問いを受け取る」は利用できません。Plus会員になると、いつでも新しい問いを生成できます。",
            "paywall_button": "Plus会員になる",
            "paywall_alert_title": "Plus会員が必要です",
            "paywall_alert_text": "現在のプランでは「別の問いを受け取る」は利用できません。\n\nアカウント画面からプランをご確認ください。",
            "footer_text": "※ Deep Insight の回答は MyProfile の分析に活用されます。MyWeb のレポートには反映されません。",
        }

    return {
        "version": "deep_insight.ui.v1",
        "lang": lang_norm,
        "max_questions": int(max_questions),
        "max_depth": int(max_depth),
        # Phase5.3: 質問文の文体/セットをサーバ側で切り替える
        # - 質問セット: DEEP_INSIGHT_QUESTION_SET_ID=v2 -> deep_insight_questions.v2.json を読む（存在すれば）
        # - 文体テンプレ: DEEP_INSIGHT_QTEXT_TEMPLATE_ID=deep_insight_qtext_ja_gentle_v1 など
        "question_set_id": str(os.getenv("DEEP_INSIGHT_QUESTION_SET_ID", "") or "").strip() or "default",
        "question_text_template_id": str(
            os.getenv("DEEP_INSIGHT_QTEXT_TEMPLATE_ID", "deep_insight_qtext_passthrough_v1")
            or "deep_insight_qtext_passthrough_v1"
        ).strip()
        or "deep_insight_qtext_passthrough_v1",
                "strategy_config": build_deep_insight_strategy_config(),
"rules": {
            # フロント側の初期値。安全側。
            "default_is_secret": True,
            # 将来：secret toggle を消したい場合などに使える
            "show_secret_toggle": True,
        },
        "strings": strings,
    }



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
        # Phase8: active_users を更新（best-effort）
        try:
            await touch_active_user(user_id, activity="deep_insight_questions")
        except Exception as exc:
            logger.warning("Failed to touch active_users: %s", exc)


        # ✅ tier をサーバー側で確定（profiles.subscription_tier）
        try:
            tier_enum = await get_subscription_tier_for_user(user_id)
        except Exception as e:
            logger.warning("Failed to resolve subscription tier (fallback to FREE): %s", e)
            tier_enum = SubscriptionTier.FREE

        effective_tier = tier_enum.value

        # ✅ Phase5.2: UI設定（制御値/文言/表示ルール）をサーバ側で一元化
        ui_config = _build_ui_config(tier_enum, lang=lang)
        # Phase5.3: 質問文の文体テンプレ（サーバ側で切替）
        qtext_template_id = str(ui_config.get("question_text_template_id") or "").strip() or "deep_insight_qtext_passthrough_v1"

        # クライアントが指定しても、サーバ側の上限で必ずクランプ（必要なら小さくはできる）
        try:
            req_max_q = int(max_questions)
        except Exception:
            req_max_q = int(ui_config.get("max_questions") or 3)
        try:
            req_max_d = int(max_depth)
        except Exception:
            req_max_d = int(ui_config.get("max_depth") or 1)

        allowed_q = int(ui_config.get("max_questions") or 3)
        allowed_d = int(ui_config.get("max_depth") or 1)
        applied_max_questions = max(1, min(req_max_q, allowed_q))
        applied_max_depth = max(1, min(req_max_d, allowed_d))

        # ✅ free: 同日中は同じバッチを返す（1日1回 = 再生成不可）
        if tier_enum == SubscriptionTier.FREE:
            hit, qids, generated_at = _get_cached_batch_if_free(user_id)
            if hit and qids:
                items: List[DeepInsightQuestionItem] = []
                for qid in qids[: max(1, int(applied_max_questions))]:
                    tpl = template_store.find_by_id(qid) if qid else None
                    if not isinstance(tpl, dict):
                        continue

                    base_text = str(tpl.get("text") or "").strip()
                    text = render_deep_insight_question_text(
                        qtext_template_id,
                        core_text=base_text,
                        structure_key=(str(tpl.get("structure_key") or "").strip() or None),
                        hint=(str(tpl.get("hint") or "").strip() or None),
                        strategy=(str(tpl.get("strategy") or "unexplored").strip() or "unexplored"),
                        depth=int(tpl.get("depth") or 1),
                        lang=lang,
                    )
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
                            "ui_config": ui_config,
                            "question_text_template_id": qtext_template_id,
                            "applied_max_questions": applied_max_questions,
                            "applied_max_depth": applied_max_depth,
                        },
                    )

        # 生成（free は「今日初回」だけ到達 / plus, premium は毎回生成できる）
        astor_req = AstorRequest(
            mode=AstorMode.DEEP_INSIGHT,
            user_id=user_id,
            options={
                "max_questions": applied_max_questions,
                "max_depth": applied_max_depth,
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
                    qd = dict(q)
                    qd["text"] = render_deep_insight_question_text(
                        qtext_template_id,
                        core_text=str(qd.get("text") or "").strip(),
                        structure_key=(str(qd.get("structure_key") or "").strip() or None),
                        hint=(str(qd.get("hint") or "").strip() or None),
                        strategy=(str(qd.get("strategy") or "").strip() or None),
                        depth=(int(qd.get("depth") or 1) if qd.get("depth") is not None else 1),
                        lang=lang,
                    )
                    questions.append(DeepInsightQuestionItem(**qd))
                except Exception:
                    continue

        # フロントがUI制御に使える情報を付与
        meta["tier"] = effective_tier
        meta["cached"] = False
        meta["can_regenerate"] = (tier_enum != SubscriptionTier.FREE)
        meta["ui_config"] = ui_config
        meta["question_text_template_id"] = qtext_template_id
        meta["applied_max_questions"] = applied_max_questions
        meta["applied_max_depth"] = applied_max_depth

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
        # Phase8: active_users を更新（best-effort）
        try:
            await touch_active_user(user_id, activity="deep_insight_answers")
        except Exception as exc:
            logger.warning("Failed to touch active_users: %s", exc)

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
                # UI側の固定文を減らす（アプリ更新無しで文面を変えられるようにする）
                "ui_message": "ありがとう。ASTORが静かに受け取りました。",
            },
        )
