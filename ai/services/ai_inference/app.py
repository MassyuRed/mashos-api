# -*- coding: utf-8 -*-
"""
Cocolon MyModel Inference API (Release-oriented)
------------------------------------------------
- POST /mymodel/infer : structure-first, privacy-preserving response
- GET  /healthz      : health check
Notes:
- No conversational memory (stateless)
- Rejects date-like/temporal queries and under-informative prompts
- Does NOT persist user content (privacy by design)
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Literal, Tuple

import httpx

from fastapi import FastAPI, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from middleware_active_user_touch import install_active_user_touch_middleware
from pydantic import BaseModel, Field
from structure_dict import build_structure_answer
from api_emotion_submit import (
    register_emotion_submit_routes,
    _extract_bearer_token,
    _resolve_user_id_from_token,
    _ensure_supabase_config,
)
from api_emotion_secret import register_emotion_secret_routes
from api_emotion_history_search import register_emotion_history_search_routes
from api_friends import register_friend_routes
from api_myprofile import register_myprofile_routes
from api_public_profile import register_public_profile_routes
from api_deep_insight import register_deep_insight_routes
from api_subscription import register_subscription_routes
from api_myweb_reports import register_myweb_report_routes, _build_target_period as _myweb_build_target_period
from api_cron_distribution import register_cron_distribution_routes
from api_ranking import register_ranking_routes
from api_ranking_mymodel_views import register_ranking_mymodel_views_routes
from api_ranking_mymodel_resonances import register_ranking_mymodel_resonances_routes
from api_ranking_mymodel_discoveries import register_ranking_mymodel_discoveries_routes

# Optional: login streak routes may live in a dedicated module in some deployments.
try:
    from api_ranking_login_streak import register_ranking_login_streak_routes  # type: ignore
except Exception:
    register_ranking_login_streak_routes = None  # type: ignore

try:
    from api_ranking_login_streak import register_ranking_routes as register_ranking_routes_login_streak  # type: ignore
except Exception:
    register_ranking_routes_login_streak = None  # type: ignore
from api_activity_login import register_activity_login_routes
from api_account_status import register_account_status_routes
from api_account_visibility import register_account_visibility_routes
from api_mymodel_create import register_mymodel_create_routes
from api_mymodel_qna import register_mymodel_qna_routes
from prompt_templates import render_prompt_template, list_prompt_templates
from astor_myprofile_persona import build_persona_context_payload
from astor_myweb_insight import generate_myweb_insight_text
from astor_myprofile_report import (
    is_myprofile_monthly_report_instruction,
    build_myprofile_monthly_report,
)
from astor_core import AstorEngine, AstorRequest, AstorMode

try:
    from astor_job_queue import enqueue_job  # type: ignore
except Exception:
    enqueue_job = None  # type: ignore

APP_NAME = os.getenv("MYMODEL_APP_NAME", "Cocolon MyModel")
PORT = int(os.getenv("MYMODEL_PORT", "8765"))
HOST = os.getenv("MYMODEL_HOST", "0.0.0.0")
# For release, set MYMODEL_CORS_ORIGINS to a comma-separated list of allowed origins.
ALLOWED_ORIGINS_RAW = os.getenv("MYMODEL_CORS_ORIGINS", "*")
ALLOWED_ORIGINS = [o.strip() for o in ALLOWED_ORIGINS_RAW.split(",")] if ALLOWED_ORIGINS_RAW else ["*"]

# Supabase (for MyProfileID access control)
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# Internal rollover (Cron -> single server entry)
INTERNAL_ROLLOVER_TOKEN = (
    os.getenv("INTERNAL_ROLLOVER_TOKEN", "").strip()
    or os.getenv("CRON_INTERNAL_TOKEN", "").strip()
    or os.getenv("INTERNAL_API_TOKEN", "").strip()
)
ACTIVE_USERS_TABLE = (os.getenv("ACTIVE_USERS_TABLE") or "active_users").strip() or "active_users"
try:
    ROLLOVER_ACTIVE_USERS_LIMIT = int(os.getenv("ROLLOVER_ACTIVE_USERS_LIMIT", "10000") or "10000")
except Exception:
    ROLLOVER_ACTIVE_USERS_LIMIT = 10000
ROLLOVER_SELF_STRUCTURE_MONTHLY_URL = os.getenv("ROLLOVER_SELF_STRUCTURE_MONTHLY_URL", "").strip()
JST = timezone(timedelta(hours=9))
GLOBAL_SUMMARY_TABLE = (os.getenv("GLOBAL_SUMMARY_TABLE") or "daily_global_activity").strip() or "daily_global_activity"
GLOBAL_SUMMARY_REFRESH_RPC = (os.getenv("GLOBAL_SUMMARY_REFRESH_RPC") or "refresh_daily_global_activity").strip() or "refresh_daily_global_activity"
GLOBAL_SUMMARY_DB_TZ = "Asia/Tokyo"
GLOBAL_SUMMARY_RESPONSE_TZ = "+09:00"

# ---------- App ----------
app = FastAPI(title=APP_NAME, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Phase8++: global active_users touch middleware (best-effort)
install_active_user_touch_middleware(app)


register_emotion_submit_routes(app)
register_emotion_secret_routes(app)
register_emotion_history_search_routes(app)
register_friend_routes(app)
register_myprofile_routes(app)
register_public_profile_routes(app)
register_deep_insight_routes(app)
register_subscription_routes(app)
register_myweb_report_routes(app)
register_cron_distribution_routes(app)
register_ranking_routes(app)
register_activity_login_routes(app)
register_account_status_routes(app)
register_account_visibility_routes(app)
register_mymodel_create_routes(app)
register_mymodel_qna_routes(app)

# Extra ranking routes (Phase: MyModel views/resonances + login streak)
# NOTE: Some ranking endpoints live in separate modules; ensure they are registered.
def _route_exists(_path: str, _method: str) -> bool:
    for _r in app.router.routes:
        if getattr(_r, "path", None) == _path and _method in getattr(_r, "methods", set()):
            return True
    return False

if not _route_exists("/ranking/mymodel_views", "GET"):
    register_ranking_mymodel_views_routes(app)

if not _route_exists("/ranking/mymodel_resonances", "GET"):
    register_ranking_mymodel_resonances_routes(app)

if not _route_exists("/ranking/mymodel_discoveries", "GET"):
    register_ranking_mymodel_discoveries_routes(app)

# /ranking/login_streak may already exist in api_ranking.py; register it here only if missing.
if not _route_exists("/ranking/login_streak", "GET"):
    if callable(register_ranking_login_streak_routes):
        register_ranking_login_streak_routes(app)  # type: ignore
    elif callable(register_ranking_routes_login_streak):
        # Fallback: module may expose register_ranking_routes (includes login_streak).
        register_ranking_routes_login_streak(app)  # type: ignore


# ASTOR engine for MyWeb insight (構造分析レポート用)
astor_myweb_engine = AstorEngine()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("mymodel")

# ---------- Models ----------
class InputPayload(BaseModel):
    period: Optional[str] = Field(default="30d", description="分析対象期間（例: 7d/30d/12w/3m）")
    ratios: Optional[Dict[str, float]] = Field(default=None, description="感情別割合（例: {'Sadness':0.4,'Calm':0.2}）")
    time_bias: Optional[List[str]] = Field(default=None, description="時間帯バイアス（例: ['morning','evening']）")
    hot_words: Optional[List[str]] = Field(default=None, description="観測語（例: ['孤独','疲労']）")

class InferRequest(BaseModel):
    instruction: Optional[str] = Field(
        default=None,
        description="一問一答の照会文（時系列を含まないこと）。template_id を使う場合は省略可",
    )
    template_id: Optional[str] = Field(
        default=None,
        description="サーバ側テンプレID（例: myprofile_qna_v1）。instruction の代わりに指定できます。",
    )
    template_vars: Optional[Dict[str, Any]] = Field(
        default=None,
        description="テンプレへ渡す変数（例: {question: \"...\"}）。省略可。",
    )
    input: Optional[InputPayload] = Field(default=None, description="分析の補助特徴量（省略可）")
    target: Optional[Literal["self", "external"]] = Field(default="self", description="自己/他者（外部）")
    user_id: Optional[str] = Field(default=None, description="ASTOR連携用のユーザーID（任意）")
    report_mode: Optional[str] = Field(default=None, description="MyProfile出力モード（light|standard|deep）。サブスクTierで制御されます")


class InferResponse(BaseModel):
    output: str
    meta: Dict[str, Any] = {}


class GlobalSummaryResponse(BaseModel):
    date: str
    tz: str = GLOBAL_SUMMARY_RESPONSE_TZ
    emotion_users: int = 0
    reflection_views: int = 0
    echo_count: int = 0
    discovery_count: int = 0
    updated_at: Optional[str] = None


# ---------- Rules & Utilities ----------
DATE_WORDS = re.compile(r"(いつ|何日|何時|何年度|何年|昨日|明日|先週|来週|先月|来月|去年|来年)")
ISO_DATE = re.compile(r"\b\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2}\b")
JP_DATE = re.compile(r"\b\d{1,2}\s*月\s*\d{1,2}\s*日\b")
MD_DATE = re.compile(r"\b\d{1,2}[-/]\d{1,2}\b")

def contains_date_like(text: str) -> bool:
    return bool(ISO_DATE.search(text) or JP_DATE.search(text) or MD_DATE.search(text) or DATE_WORDS.search(text))


def _sb_headers_json(*, prefer: Optional[str] = None) -> Dict[str, str]:
    """Supabase PostgREST 用の service_role ヘッダ。"""
    _ensure_supabase_config()
    h = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


async def _sb_get(path: str, *, params: Optional[Dict[str, str]] = None) -> httpx.Response:
    _ensure_supabase_config()
    url = f"{SUPABASE_URL}{path}"
    async with httpx.AsyncClient(timeout=8.0) as client:
        return await client.get(url, headers=_sb_headers_json(), params=params)


async def _sb_post(
    path: str, *, json: Any, params: Optional[Dict[str, str]] = None, prefer: Optional[str] = None
) -> httpx.Response:
    _ensure_supabase_config()
    url = f"{SUPABASE_URL}{path}"
    async with httpx.AsyncClient(timeout=8.0) as client:
        return await client.post(url, headers=_sb_headers_json(prefer=prefer), params=params, json=json)


async def _sb_post_rpc(fn: str, payload: Dict[str, Any]) -> httpx.Response:
    return await _sb_post(f"/rest/v1/rpc/{fn}", json=payload)


def _normalize_global_summary_tz(raw_tz: Optional[str]) -> Tuple[str, str]:
    s = str(raw_tz or "").strip()
    if not s:
        return (GLOBAL_SUMMARY_DB_TZ, GLOBAL_SUMMARY_RESPONSE_TZ)

    normalized = s.replace(" ", "")
    if normalized in {"Asia/Tokyo", "asia/tokyo", "JST", "jst", "+09:00", "+0900", "09:00"}:
        return (GLOBAL_SUMMARY_DB_TZ, GLOBAL_SUMMARY_RESPONSE_TZ)

    raise HTTPException(status_code=400, detail="Only Asia/Tokyo (+09:00) is supported currently")


def _resolve_global_summary_date(raw_date: Optional[str]) -> str:
    s = str(raw_date or "").strip()
    if not s:
        return datetime.now(JST).date().isoformat()

    try:
        return datetime.strptime(s, "%Y-%m-%d").date().isoformat()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD") from exc


def _global_summary_zero(*, activity_date: str, response_tz: str) -> GlobalSummaryResponse:
    return GlobalSummaryResponse(
        date=activity_date,
        tz=response_tz,
        emotion_users=0,
        reflection_views=0,
        echo_count=0,
        discovery_count=0,
        updated_at=None,
    )


def _parse_global_summary_row(row: Dict[str, Any], *, fallback_date: str, response_tz: str) -> GlobalSummaryResponse:
    try:
        emotion_users = int((row or {}).get("emotion_users") or 0)
    except Exception:
        emotion_users = 0
    try:
        reflection_views = int((row or {}).get("reflection_view_count") or 0)
    except Exception:
        reflection_views = 0
    try:
        echo_count = int((row or {}).get("echo_count") or 0)
    except Exception:
        echo_count = 0
    try:
        discovery_count = int((row or {}).get("discovery_count") or 0)
    except Exception:
        discovery_count = 0

    date_value = str((row or {}).get("activity_date") or fallback_date).strip() or fallback_date
    updated_at_raw = (row or {}).get("updated_at")
    updated_at = None if updated_at_raw is None else (str(updated_at_raw).strip() or None)

    return GlobalSummaryResponse(
        date=date_value,
        tz=response_tz,
        emotion_users=emotion_users,
        reflection_views=reflection_views,
        echo_count=echo_count,
        discovery_count=discovery_count,
        updated_at=updated_at,
    )


async def _fetch_global_summary_row(*, activity_date: str, db_tz: str) -> Optional[Dict[str, Any]]:
    resp = await _sb_get(
        f"/rest/v1/{GLOBAL_SUMMARY_TABLE}",
        params={
            "select": "activity_date,tz,emotion_users,reflection_view_count,echo_count,discovery_count,updated_at",
            "activity_date": f"eq.{activity_date}",
            "tz": f"eq.{db_tz}",
            "limit": "1",
        },
    )
    if resp.status_code >= 300:
        logger.warning(
            "Supabase %s select failed (global summary): %s %s",
            GLOBAL_SUMMARY_TABLE,
            resp.status_code,
            (resp.text or "")[:800],
        )
        return None

    rows = resp.json()
    if isinstance(rows, list) and rows and isinstance(rows[0], dict):
        return rows[0]
    return None


async def _refresh_global_summary_row(*, activity_date: str, db_tz: str) -> Optional[Dict[str, Any]]:
    try:
        resp = await _sb_post_rpc(
            GLOBAL_SUMMARY_REFRESH_RPC,
            {
                "p_activity_date": activity_date,
                "p_tz": db_tz,
            },
        )
    except Exception as exc:
        logger.warning("global summary refresh RPC failed (network): %s", exc)
        return None

    if resp.status_code >= 300:
        logger.warning(
            "Supabase rpc %s failed (global summary refresh): %s %s",
            GLOBAL_SUMMARY_REFRESH_RPC,
            resp.status_code,
            (resp.text or "")[:800],
        )
        return None

    try:
        data = resp.json()
    except Exception:
        return None

    if isinstance(data, dict):
        return data
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return data[0]
    return None


async def _has_myprofile_link(*, viewer_user_id: str, owner_user_id: str) -> bool:
    """viewer -> owner のアクセス許可があるか（myprofile_links で判定）。"""
    resp = await _sb_get(
        "/rest/v1/myprofile_links",
        params={
            "select": "viewer_user_id",
            "viewer_user_id": f"eq.{viewer_user_id}",
            "owner_user_id": f"eq.{owner_user_id}",
            "limit": "1",
        },
    )
    if resp.status_code >= 300:
        logger.error(
            "Supabase myprofile_links select failed: %s %s",
            resp.status_code,
            resp.text[:1500],
        )
        raise HTTPException(status_code=502, detail="Failed to check myprofile link")
    rows = resp.json()
    return bool(isinstance(rows, list) and rows)

async def _fetch_latest_monthly_report_text(*, user_id: str) -> Optional[str]:
    """差分要約用に、直近の月次レポ本文を取得する（self のみで使用）。

    - report_type="monthly"
    - content_text を返す（無ければ None）
    """
    uid = str(user_id or "").strip()
    if not uid:
        return None
    try:
        resp = await _sb_get(
            "/rest/v1/myprofile_reports",
            params={
                "select": "content_text,period_end",
                "user_id": f"eq.{uid}",
                "report_type": "eq.monthly",
                "order": "period_end.desc",
                "limit": "1",
            },
        )
        if resp.status_code >= 300:
            logger.warning("Supabase myprofile_reports select failed: %s %s", resp.status_code, resp.text[:500])
            return None
        rows = resp.json()
        if isinstance(rows, list) and rows:
            txt = rows[0].get("content_text") or ""
            txt = str(txt)
            # 解析に十分な範囲だけ（重すぎないように）
            return txt[:8000]
    except Exception as exc:
        logger.warning("Failed to fetch previous monthly report: %s", exc)
    return None

def _iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _require_internal_rollover_auth(authorization: Optional[str]) -> None:
    expected = str(INTERNAL_ROLLOVER_TOKEN or "").strip()
    if not expected:
        raise HTTPException(status_code=500, detail="Internal rollover token is not configured")

    actual = _extract_bearer_token(authorization) if authorization else None
    if not actual or str(actual).strip() != expected:
        raise HTTPException(status_code=401, detail="Invalid internal rollover token")


async def _fetch_active_user_ids(*, limit: int = ROLLOVER_ACTIVE_USERS_LIMIT) -> List[str]:
    resp = await _sb_get(
        f"/rest/v1/{ACTIVE_USERS_TABLE}",
        params={
            "select": "user_id",
            "limit": str(max(1, int(limit or 1))),
        },
    )
    if resp.status_code >= 300:
        logger.error(
            "Supabase active_users select failed: %s %s",
            resp.status_code,
            resp.text[:1500],
        )
        raise HTTPException(status_code=502, detail="Failed to fetch active users")

    rows = resp.json()
    out: List[str] = []
    seen = set()
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            uid = str(row.get("user_id") or "").strip()
            if not uid or uid in seen:
                continue
            seen.add(uid)
            out.append(uid)
    return out


def _build_rollover_plan(now_utc: datetime) -> Dict[str, Any]:
    now_jst = now_utc.astimezone(JST)

    daily_target = _myweb_build_target_period("daily", now_utc)
    daily_day_jst = daily_target.period_start_utc.astimezone(JST)
    daily_scope = f"emotion_daily:{daily_day_jst.year:04d}-{daily_day_jst.month:02d}-{daily_day_jst.day:02d}"

    weekly_scope: Optional[str] = None
    if now_jst.weekday() == 6:
        weekly_target = _myweb_build_target_period("weekly", now_utc)
        weekly_dist_jst = weekly_target.dist_utc.astimezone(JST)
        weekly_scope = f"emotion_weekly:{weekly_dist_jst.year:04d}-{weekly_dist_jst.month:02d}-{weekly_dist_jst.day:02d}"

    monthly_scope: Optional[str] = None
    run_self_structure_monthly = False
    if now_jst.day == 1:
        monthly_target = _myweb_build_target_period("monthly", now_utc)
        monthly_end_jst = monthly_target.period_end_utc.astimezone(JST)
        monthly_scope = f"emotion_monthly:{monthly_end_jst.year:04d}-{monthly_end_jst.month:02d}"
        run_self_structure_monthly = True

    return {
        "now_jst": now_jst.isoformat(),
        "daily_scope": daily_scope,
        "weekly_scope": weekly_scope,
        "monthly_scope": monthly_scope,
        "run_self_structure_monthly": run_self_structure_monthly,
    }


async def _enqueue_rollover_snapshot_job(*, user_id: str, scope: str, requested_at: str) -> None:
    if not callable(enqueue_job):
        raise HTTPException(status_code=500, detail="astor_job_queue.enqueue_job is unavailable")

    uid = str(user_id or "").strip()
    sc = str(scope or "").strip()
    if not uid or not sc:
        raise HTTPException(status_code=400, detail="user_id and scope are required")

    await enqueue_job(
        job_key=f"snapshot_generate_v1:{uid}:{sc}",
        job_type="snapshot_generate_v1",
        user_id=uid,
        payload={
            "scope": sc,
            "trigger": "internal_rollover",
            "requested_at": requested_at,
        },
        priority=12,
    )


async def _trigger_self_structure_monthly_rollover(*, requested_at: str) -> Dict[str, Any]:
    url = str(ROLLOVER_SELF_STRUCTURE_MONTHLY_URL or "").strip()
    if not url:
        return {
            "due": True,
            "status": "skipped",
            "reason": "ROLLOVER_SELF_STRUCTURE_MONTHLY_URL is not configured",
        }

    headers = {"Content-Type": "application/json"}
    if INTERNAL_ROLLOVER_TOKEN:
        headers["Authorization"] = f"Bearer {INTERNAL_ROLLOVER_TOKEN}"

    body = {
        "trigger": "internal_rollover",
        "requested_at": requested_at,
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(url, headers=headers, json=body)
    except Exception as exc:
        return {
            "due": True,
            "status": "failed",
            "reason": str(exc),
        }

    return {
        "due": True,
        "status": "ok" if 200 <= resp.status_code < 300 else "failed",
        "http_status": int(resp.status_code),
        "body": (resp.text or "")[:500],
    }


def load_default_features() -> Dict[str, Any]:
    """Attempt to load default features from common repo layouts."""
    candidates = [
        Path(__file__).parent / "ai" / "data" / "processed" / "features.json",           # repo root/ai/...
        Path(__file__).parent / "mashos" / "ai" / "data" / "processed" / "features.json",# repo root/mashos/ai/...
        Path.cwd() / "ai" / "data" / "processed" / "features.json",
        Path.cwd() / "mashos" / "ai" / "data" / "processed" / "features.json",
    ]
    for p in candidates:
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning("Failed to read features.json at %s: %s", p, e)
    # Safe fallback
    return {"period": "30d", "ratios": {"Calm": 0.34, "Joy": 0.24, "Sadness": 0.22, "Anxiety": 0.20}}

def top_emotions(ratios: Dict[str, float], n: int = 2) -> List[str]:
    return [k for k, _ in sorted(ratios.items(), key=lambda kv: kv[1], reverse=True)[:n]] if ratios else []

def intensity_from_len(text: str) -> str:
    n = len(re.sub(r"\s+", "", text))
    return "強い" if n > 60 else "中程度の" if n > 30 else "弱い"


def _short_structure_gloss_for_qa(struct_key: str) -> str:
    """構造辞書があれば、短い説明（1行）を返す（MyProfile 一問一答用）。

    - Standard/Deep のときのみ利用する想定。
    - 辞書が無い/該当エントリが無い場合は空文字。
    """

    try:
        from structure_dict import load_structure_dict  # local module
    except Exception:
        return ""

    try:
        d = load_structure_dict() or {}
        entry = d.get(struct_key)
        if not isinstance(entry, dict):
            return ""
        secs = entry.get("sections") or {}
        defin = str(secs.get("定義") or "").strip()
        if not defin:
            return ""
        # 先頭1文っぽく切る（長すぎないように）
        defin = re.split(r"[。\n]", defin)[0].strip()
        return defin[:64] if defin else ""
    except Exception:
        return ""


def compose_response(
    instr: str,
    payload: Optional[InputPayload],
    target: str,
    persona_ctx: Optional[Dict[str, Any]] = None,
    report_mode: Optional[str] = "light",
) -> str:
    """MyProfile 一問一答（深掘り）用の応答文を作る。

    v0.x の rule ベースでも「答えが明示される体験」を作れるように、
    先頭に結論（答え）→ 構造仮説 → 根拠 → 微調整 → 観測 の順で返す。
    """
    import os

    # ---- 入力の整形（テンプレに埋め込まれている場合の抽出） ----
    raw = (instr or "").strip()
    q = raw
    # 生成テンプレに埋めた場合
    for marker in ["【質問】", "<USER_QUESTION>", "<QUESTION>"]:
        if marker in q:
            q = q.split(marker)[-1].strip()
    if not q:
        q = raw

    # ---- 特徴量（感情傾向は補助的に使う） ----
    features = payload.dict() if payload else {}
    defaults = load_default_features()
    ratios = features.get("ratios") or defaults.get("ratios") or {}
    time_bias = features.get("time_bias") or []
    hot_words = features.get("hot_words") or []

    lang = detect_lang(q)

    # ---- report_mode（Light / Standard / Deep）----
    # Step 4: 一問一答も3モードに対応。
    # - Light: 構造辞書(gloss)なし / Deep追加なし
    # - Standard: glossあり（読み手が置いていかれない密度で）
    # - Deep: Standard + MashLogic追記（別モジュールで分離）
    # Default is Light to preserve the legacy (pre-mode) behavior.
    mode = "light"
    try:
        from subscription import MyProfileMode, normalize_myprofile_mode

        mode = normalize_myprofile_mode(report_mode, default=MyProfileMode.LIGHT).value
    except Exception:
        # Fallback (be permissive but safe)
        s = str(report_mode or "").strip()
        s2 = s.lower()
        if s2 in ("light", "standard", "deep"):
            mode = s2
        elif s in ("ライト", "Light"):
            mode = "light"
        elif s in ("スタンダード", "Standard"):
            mode = "standard"
        elif s in ("ディープ", "Deep"):
            mode = "deep"
        else:
            mode = "light"

    use_structure_gloss = (lang == "ja") and (mode != "light")
    use_mashlogic = (lang == "ja") and (mode == "deep")

    def _fmt_key(k: str) -> str:
        """Format a structure key with optional short gloss."""

        kk = str(k or "").strip()
        if not kk:
            return ""
        if not use_structure_gloss:
            return kk
        g = _short_structure_gloss_for_qa(kk)
        if not g:
            return kk
        # keep it short (already trimmed in helper)
        return f"{kk}（意味: {g}）"

    # 上位感情（最大2）
    def top2(d):
        return [k for k, _ in sorted((d or {}).items(), key=lambda kv: kv[1], reverse=True)[:2]]

    tops = top2(ratios)
    e1 = tops[0] if len(tops) > 0 else None
    e2 = tops[1] if len(tops) > 1 else None

    EMO_JA = {"Joy": "喜び", "Sadness": "悲しみ", "Anxiety": "不安", "Anger": "怒り", "Calm": "落ち着き"}
    def emo_label_jp(x: Optional[str]) -> str:
        return EMO_JA.get(str(x or ""), "感情")

    def intensity_label(x: float) -> str:
        if x >= 2.6:
            return "強め"
        if x >= 1.9:
            return "中くらい"
        if x >= 1.2:
            return "やわらかめ"
        return "かなりやわらかめ"

    # ---- persona context（構造傾向/Deep Insight） ----
    structures = []
    deep_answers = []
    if persona_ctx and isinstance(persona_ctx, dict):
        structures = persona_ctx.get("structures") or []
        deep_bundle = persona_ctx.get("deep_insight") or {}
        if isinstance(deep_bundle, dict):
            deep_answers = deep_bundle.get("answers") or []

    top_keys: List[str] = []
    top_meta: List[Tuple[str, float]] = []  # (key, avg_intensity)
    for s in (structures or [])[:3]:
        if not isinstance(s, dict):
            continue
        k = str(s.get("key") or "").strip()
        if not k:
            continue
        top_keys.append(k)
        try:
            top_meta.append((k, float(s.get("avg_intensity") or 0.0)))
        except Exception:
            top_meta.append((k, 0.0))

    # ---- 口調/呼称 ----
    user_name = os.getenv("MYMODEL_USER_NAME", None)
    you = user_name if (user_name and lang == "ja") else ("you" if lang == "en" else "あなた")

    # ---- ざっくり質問タイプ推定（“答え感”を作るため） ----
    qtype = "general"
    if re.search(r"どっち|選ぶ|迷", q):
        qtype = "decision"
    elif re.search(r"どうすれば|どうしたら|したらいい|すればいい", q):
        qtype = "action"
    elif re.search(r"なぜ|原因|理由", q):
        qtype = "why"

    # ---- 結論（答え） ----
    conclusion: List[str] = []
    if lang != "ja":
        # minimal EN support (keep it short)
        core = (top_keys[0] if top_keys else "your current pattern")
        conclusion.append(f"This question likely appears when {core} is active.")
        conclusion.append("Try separating the trigger and your interpretation before deciding.")
    else:
        if qtype == "decision":
            conclusion.append("結論: いまは『基準を1つ言語化 → 小さく試す』が一番確実です。")
        elif qtype == "action":
            conclusion.append("結論: まず『刺激→解釈→感情→行動』を1行ずつ書くと、次の一手が決まります。")
        elif qtype == "why":
            conclusion.append("結論: 原因は1つに断定せず、『よく出る構造 × 直前の刺激』として観測すると近道です。")
        else:
            conclusion.append("結論: この問いは、自己構造の“前提”が揺れているサインです。前提を1行で仮置きすると整理が進みます。")

        if top_keys:
            conclusion.append(
                f"（補助: 最近は『{_fmt_key(top_keys[0])}』が立ちやすい傾向があり、その影響下で出ている問いかもしれません）"
            )

    # ---- 仮説（刺激→認知→感情→行動） ----
    emo_phrase = None
    if lang == "ja":
        if e1 and e2:
            emo_phrase = f"{emo_label_jp(e1)}/{emo_label_jp(e2)}"
        elif e1:
            emo_phrase = emo_label_jp(e1)
    else:
        if e1 and e2:
            emo_phrase = f"{e1}/{e2}"
        elif e1:
            emo_phrase = str(e1)

    hypo: List[str] = []
    if lang == "ja":
        core_k = _fmt_key(top_keys[0]) if top_keys else "（未特定）"
        hypo.append(f"・刺激: （例）評価/比較/未確定/期待のズレ など")
        hypo.append(f"・認知: （仮）『{core_k}』の判断が入って、意味づけが急に固定されやすい")
        if emo_phrase:
            hypo.append(f"・感情: {emo_phrase} に寄りやすい")
        hypo.append("・行動: （仮）確認/修正へ向かう、または一時停止して距離を取る")
    else:
        hypo.append("- Trigger: e.g., evaluation / comparison / uncertainty")
        hypo.append("- Interpretation: a quick, fixed meaning-making")
        if emo_phrase:
            hypo.append(f"- Feeling: {emo_phrase}")
        hypo.append("- Action: checking / correcting, or pausing")

    # ---- 根拠 ----
    evidence: List[str] = []
    if lang == "ja":
        if top_meta:
            for k, inten in top_meta[:2]:
                evidence.append(f"・構造傾向: 『{_fmt_key(k)}』が出やすい（強度: {intensity_label(inten)}）")
        if hot_words:
            evidence.append(f"・観測語: { '、'.join(hot_words[:3]) } が登場しやすい")
        if deep_answers:
            a0 = next((a for a in deep_answers if isinstance(a, dict) and str(a.get("text") or "").strip()), None)
            if a0:
                txt = str(a0.get("text") or "").strip()
                if len(txt) > 80:
                    txt = txt[:80] + "…"
                evidence.append(f"・Deep Insight: 最近の言語化（抜粋）『{txt}』")
        if not evidence:
            evidence.append("・観測材料: まだ少なめ（入力が増えるほど精度が上がります）")
    else:
        if top_meta:
            for k, _ in top_meta[:2]:
                evidence.append(f"- Structure: {k} tends to appear")
        if not evidence:
            evidence.append("- Evidence is limited; more logs improve accuracy.")

    # ---- 微調整 ----
    tweaks: List[str] = []
    if lang == "ja":
        tweaks.append("・結論を急がず『仮置き』を許可する（いまは1回で決めない）")
        tweaks.append("・刺激と解釈を分けて書く（解釈は“仮説”として扱う）")
        tweaks.append("・強い日は、先に身体（睡眠/空腹/疲労）を整えてから判断する")
        if time_bias:
            TB_JA = {"morning": "朝", "noon": "昼", "afternoon": "午後", "evening": "夕方", "night": "夜", "midnight": "深夜"}
            mapped = [TB_JA.get(b, b) for b in time_bias[:3]]
            tweaks.append(f"・{ '、'.join(mapped) }は揺れやすい可能性があるので、重要判断は避ける")
    else:
        tweaks.append("- Avoid forcing a final decision; keep it provisional.")
        tweaks.append("- Separate trigger and interpretation.")
        tweaks.append("- Stabilize basic body needs before judging.")

    # ---- 次の観測 ----
    observe: List[str] = []
    if lang == "ja":
        observe.append("・刺激: 何が起きたか（1語）")
        observe.append("・解釈: どう意味づけたか（1文）")
        observe.append("・身体: 眠気/空腹/疲労の有無（○×）")
    else:
        observe.append("- Trigger: what happened (one phrase)")
        observe.append("- Interpretation: one sentence")
        observe.append("- Body: sleep/hunger/fatigue (yes/no)")

    # ---- 追加質問（精度を上げる） ----
    followups: List[str] = []
    if lang == "ja":
        followups.append("・いまの場面は『評価される/比較される』が関係していますか？")
        followups.append("・この問いの直前に“何を守りたかったか”を1語で言うなら？")
    else:
        followups.append("- Is evaluation/comparison involved in this situation?")
        followups.append("- What were you trying to protect (one word)?")

    # ---- 出力 ----
    if lang != "ja":
        parts = [
            "[Conclusion]",
            "\n".join(conclusion),
            "\n[Hypothesis]",
            "\n".join(hypo),
            "\n[Evidence]",
            "\n".join(evidence),
            "\n[Micro-adjustments]",
            "\n".join(tweaks),
            "\n[Next observations]",
            "\n".join(observe),
            "\n[Optional follow-ups]",
            "\n".join(followups),
        ]
        out_text = "\n".join(parts).strip()
        return out_text

    parts = [
        "【結論（答え）】",
        "\n".join(conclusion),
        "",
        "【自己構造の仮説（刺激→認知→感情→行動）】",
        "\n".join(hypo),
        "",
        "【根拠（観測として見えていること）】",
        "\n".join(evidence),
        "",
        "【安定させる微調整】",
        "\n".join(tweaks),
        "",
        "【次の観測（2〜3）】",
        "\n".join(observe),
        "",
        "【追加で確認したい点（任意・1〜2）】",
        "\n".join(followups),
    ]

    out_text = "\n".join(parts).strip()

    # Deep-only enhancer (MashLogic): keep isolated from Light/Standard
    if use_mashlogic:
        try:
            from mashlogic_qa_enhancer import enhance_myprofile_qa_response

            ctx = {
                "user_id": (persona_ctx or {}).get("user_id"),
                "mode": mode,
                "lang": lang,
                "qtype": qtype,
                "question": q,
                "top_keys": top_keys,
                "structures": structures,
                "deep_insight_answers": deep_answers,
            }
            out_text = enhance_myprofile_qa_response(out_text, ctx)
        except Exception:
            # Deep mode must degrade gracefully
            pass

    return out_text


# ---------- Add-on: Advanced date-like guard (non-destructive) ----------
# This block is auto-injected to extend date/temporal detection without removing original rules.
# It mirrors the patterns used in date_guard.py and exposes a helper used only by /mymodel/infer.
import re as _re_addon
from typing import List as _List, Tuple as _Tuple

_JA_PATTERNS_ADDON = [
    r"\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日?",
    r"\d{1,2}\s*月\s*\d{1,2}\s*日",
    r"\d{4}[-/]\d{1,2}[-/]\d{1,2}",
    r"\d{1,2}[:時]\d{2}(?:[:分]\d{2})?",
    r"(昨日|今日|明日|一昨日|明後日|先週|来週|先月|来月|去年|今年|来年)",
    r"(月|火|水|木|金|土|日)曜日",
    r"(何日|何月|何年|いつ)"
]
_EN_PATTERNS_ADDON = [
    r"\b\d{4}-\d{1,2}-\d{1,2}\b",
    r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:,\s*\d{4})?\b",
    r"\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b",
    r"\b(?:yesterday|today|tomorrow|last\s+(?:week|month|year)|next\s+(?:week|month|year))\b",
    r"\b(?:when|what\s+day|what\s+date)\b",
    r"\b\d{1,2}:\d{2}(?::\d{2})?\b"
]
_JA_RX_ADDON = [_re_addon.compile(p) for p in _JA_PATTERNS_ADDON]
_EN_RX_ADDON = [_re_addon.compile(p, flags=_re_addon.IGNORECASE) for p in _EN_PATTERNS_ADDON]

def _contains_date_like_addon(text: str, lang: str | None = None) -> _Tuple[bool, _List[str]]:
    matches: _List[str] = []
    def scan(rx_list):
        local = []
        for rx in rx_list:
            local.extend(m.group(0) for m in rx.finditer(text))
        return local
    if lang == 'ja':
        matches = scan(_JA_RX_ADDON)
    elif lang == 'en':
        matches = scan(_EN_RX_ADDON)
    else:
        matches = scan(_JA_RX_ADDON) + scan(_EN_RX_ADDON)
    return (len(matches) > 0, matches[:5])

def contains_date_like_adv(text: str) -> bool:
    # Use both the original quick rules and the extended ones
    try:
        base = contains_date_like(text)  # original
    except Exception:
        base = False
    ext, _ = _contains_date_like_addon(text, None)
    return bool(base or ext)
# ---------- End Add-on ----------





# ---------- MyWeb Insight Models ----------
class MyWebInsightRequest(BaseModel):
    user_id: Optional[str] = Field(
        default=None,
        description="ASTOR 構造分析対象のユーザーID（省略時は Authorization から解決）",
    )
    period: Optional[str] = Field(
        default="30d",
        description="分析対象期間（例: 7d/30d/12w/3m）",
    )


class MyWebInsightResponse(BaseModel):
    text: str
    meta: Dict[str, Any] = {}


# ---------- MyWeb Insight Routes ----------
@app.post("/myweb/insight", response_model=MyWebInsightResponse)
async def myweb_insight(
    req: MyWebInsightRequest,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> MyWebInsightResponse:
    """汎用 MyWeb 構造分析レポート。

    - period: "7d", "30d", "12w", "3m" など
    - user_id が指定されていない場合は Authorization: Bearer トークンから解決する。
    """
    # Authorization is required for MyWeb insight (premium feature)
    access_token = _extract_bearer_token(authorization)
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Authorization header with Bearer token is required",
        )

    try:
        viewer_user_id = await _resolve_user_id_from_token(access_token)
    except Exception as exc:
        logger.error("Failed to resolve user_id from token in /myweb/insight: %s", exc)
        raise HTTPException(status_code=401, detail="Invalid authorization token")

    # Only allow self access (prevents passing arbitrary user_id)
    user_id = req.user_id or viewer_user_id
    if req.user_id and str(req.user_id) != str(viewer_user_id):
        raise HTTPException(status_code=403, detail="user_id must match the authenticated user")

    # Subscription tier gating (Plus: Standard, Premium: Structural)
    from subscription import SubscriptionTier
    from subscription_store import get_subscription_tier_for_user

    tier_enum: SubscriptionTier = SubscriptionTier.FREE
    try:
        tier_enum = await get_subscription_tier_for_user(viewer_user_id, default=SubscriptionTier.FREE)
    except Exception as exc:
        logger.warning("Failed to resolve subscription tier; fallback to FREE: %s", exc)
        tier_enum = SubscriptionTier.FREE

    if tier_enum != SubscriptionTier.PREMIUM:
        raise HTTPException(status_code=403, detail="MyWeb insight is available for premium users only")

    astor_req = AstorRequest(
        mode=AstorMode.MYWEB_INSIGHT,
        user_id=user_id,
        period=req.period or "30d",
    )
    astor_resp = astor_myweb_engine.handle(astor_req)
    if astor_resp.text is None:
        raise HTTPException(status_code=500, detail="ASTOR MyWebInsight failed")

    meta: Dict[str, Any] = dict(astor_resp.meta or {})
    # period 情報が無ければ補完
    meta.setdefault("period", req.period or "30d")
    return MyWebInsightResponse(text=astor_resp.text, meta=meta)


@app.post("/myweb/insight/weekly", response_model=MyWebInsightResponse)
async def myweb_insight_weekly(
    req: MyWebInsightRequest,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> MyWebInsightResponse:
    """週次 MyWeb 構造分析レポート。

    period が指定されていなければ自動的に "7d" を採用する。
    """
    effective_req = MyWebInsightRequest(
        user_id=req.user_id,
        period=req.period or "7d",
    )
    return await myweb_insight(effective_req, authorization=authorization)


@app.post("/myweb/insight/monthly", response_model=MyWebInsightResponse)
async def myweb_insight_monthly(
    req: MyWebInsightRequest,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> MyWebInsightResponse:
    """月次 MyWeb 構造分析レポート。

    period が指定されていなければ自動的に "30d" を採用する。
    """
    effective_req = MyWebInsightRequest(
        user_id=req.user_id,
        period=req.period or "30d",
    )
    return await myweb_insight(effective_req, authorization=authorization)


@app.get("/myweb/insight/weekly", response_model=MyWebInsightResponse)
async def myweb_insight_weekly_get(
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> MyWebInsightResponse:
    """GET 版の週次 MyWeb 構造分析レポート。

    - ボディを送らず Authorization ヘッダだけで呼び出す互換用。
    """
    req = MyWebInsightRequest(user_id=None, period="7d")
    return await myweb_insight(req, authorization=authorization)


@app.get("/myweb/insight/monthly", response_model=MyWebInsightResponse)
async def myweb_insight_monthly_get(
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> MyWebInsightResponse:
    """GET 版の月次 MyWeb 構造分析レポート。

    - ボディを送らず Authorization ヘッダだけで呼び出す互換用。
    """
    req = MyWebInsightRequest(user_id=None, period="30d")
    return await myweb_insight(req, authorization=authorization)


@app.get("/global_summary", response_model=GlobalSummaryResponse)
async def global_summary(
    date: Optional[str] = Query(default=None, description="YYYY-MM-DD. Defaults to today in JST."),
    tz: Optional[str] = Query(default=GLOBAL_SUMMARY_RESPONSE_TZ, description="Currently fixed to +09:00 / Asia/Tokyo."),
) -> GlobalSummaryResponse:
    db_tz, response_tz = _normalize_global_summary_tz(tz)
    activity_date = _resolve_global_summary_date(date)

    try:
        row = await _fetch_global_summary_row(activity_date=activity_date, db_tz=db_tz)
        if row is None:
            row = await _refresh_global_summary_row(activity_date=activity_date, db_tz=db_tz)

        if row is None:
            return _global_summary_zero(activity_date=activity_date, response_tz=response_tz)

        return _parse_global_summary_row(row, fallback_date=activity_date, response_tz=response_tz)
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("global_summary failed: %s", exc)
        return _global_summary_zero(activity_date=activity_date, response_tz=response_tz)


@app.get("/healthz")
def healthz() -> Dict[str, Any]:
    return {"status": "ok", "app": APP_NAME}


async def _run_rollover_once() -> Dict[str, Any]:
    """Execute one rollover cycle and return a structured summary.

    This helper is shared by:
    - POST /internal/rollover (token-protected manual/internal trigger)
    - CLI command: python app.py rollover (Render Cron command mode)
    """
    now_utc = datetime.now(timezone.utc)
    requested_at = _iso_z(now_utc)
    plan = _build_rollover_plan(now_utc)
    user_ids = await _fetch_active_user_ids()

    enqueued = {
        "daily": 0,
        "weekly": 0,
        "monthly": 0,
    }
    errors: List[Dict[str, str]] = []

    for uid in user_ids:
        try:
            await _enqueue_rollover_snapshot_job(
                user_id=uid,
                scope=str(plan["daily_scope"]),
                requested_at=requested_at,
            )
            enqueued["daily"] += 1
        except Exception as exc:
            errors.append({"user_id": uid, "scope": str(plan["daily_scope"]), "error": str(exc)})

        weekly_scope = str(plan.get("weekly_scope") or "").strip()
        if weekly_scope:
            try:
                await _enqueue_rollover_snapshot_job(
                    user_id=uid,
                    scope=weekly_scope,
                    requested_at=requested_at,
                )
                enqueued["weekly"] += 1
            except Exception as exc:
                errors.append({"user_id": uid, "scope": weekly_scope, "error": str(exc)})

        monthly_scope = str(plan.get("monthly_scope") or "").strip()
        if monthly_scope:
            try:
                await _enqueue_rollover_snapshot_job(
                    user_id=uid,
                    scope=monthly_scope,
                    requested_at=requested_at,
                )
                enqueued["monthly"] += 1
            except Exception as exc:
                errors.append({"user_id": uid, "scope": monthly_scope, "error": str(exc)})

    self_structure_monthly: Dict[str, Any]
    if bool(plan.get("run_self_structure_monthly")):
        self_structure_monthly = await _trigger_self_structure_monthly_rollover(requested_at=requested_at)
    else:
        self_structure_monthly = {"due": False, "status": "not_due"}

    return {
        "status": "ok",
        "requested_at": requested_at,
        "rollover": {
            "now_jst": plan.get("now_jst"),
            "daily_scope": plan.get("daily_scope"),
            "weekly_scope": plan.get("weekly_scope"),
            "monthly_scope": plan.get("monthly_scope"),
            "self_structure_monthly_due": bool(plan.get("run_self_structure_monthly")),
        },
        "active_users": len(user_ids),
        "enqueued": enqueued,
        "self_structure_monthly": self_structure_monthly,
        "errors": errors[:100],
    }


@app.post("/internal/rollover")
async def internal_rollover(
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> Dict[str, Any]:
    """Single daily cron entry (JST 0:00) that fans out daily/weekly/monthly rollover jobs.

    Behavior:
    - Every day: enqueue emotion_daily snapshot for the previous JST day.
    - Sunday JST 00:00: additionally enqueue weekly emotion snapshot.
    - 1st JST 00:00: additionally enqueue monthly emotion snapshot.
    - Self-structure monthly is exposed as a month-start hook via URL env, because
      its existing persistence path is outside this file.
    """
    _require_internal_rollover_auth(authorization)
    return await _run_rollover_once()


def _run_rollover_cli() -> int:
    """Render Cron command entrypoint: python app.py rollover"""
    import asyncio
    try:
        result = asyncio.run(_run_rollover_once())
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception:
        logger.exception("rollover CLI failed")
        return 1


@app.get("/mymodel/templates")
def mymodel_templates() -> Dict[str, Any]:
    """Return available server-side prompt templates (Phase5)."""
    return {"status": "ok", "templates": list_prompt_templates()}


@app.post("/mymodel/infer", response_model=InferResponse)
async def infer(
    req: InferRequest,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> InferResponse:
    instr = (req.instruction or "").strip()
    if not instr:
        # Phase5: allow client to send template_id instead of raw instruction
        if req.template_id:
            try:
                instr = render_prompt_template(
                    req.template_id,
                    req.template_vars or {},
                    target=(req.target or "self"),
                ).strip()
            except HTTPException:
                raise
            except Exception as exc:
                raise HTTPException(status_code=400, detail=f"テンプレ生成に失敗しました: {exc}")
        else:
            raise HTTPException(status_code=400, detail="情報が足りないため応答できません。")

    # MyProfile（月次レポート生成）の場合は、instruction 内に日付表現（例: 12/1〜）が
    # 含まれることがあるため、日付ガードを“照会”にだけ適用する。
    is_myprofile_report = is_myprofile_monthly_report_instruction(instr)

    if len(instr) < 4:
        raise HTTPException(status_code=400, detail="情報が足りないため応答できません。")
    if (not is_myprofile_report) and contains_date_like_adv(instr):
        raise HTTPException(status_code=400, detail="この照会は受け付けられません（日付が含まれています）。")

    # --- MyProfileID（外部照会）のアクセス制御 ---
    # viewer（照会者）は Authorization から確定する。
    access_token = _extract_bearer_token(authorization) if authorization else None
    viewer_user_id: Optional[str] = None
    if access_token:
        # 不正/期限切れトークンは 401
        viewer_user_id = await _resolve_user_id_from_token(access_token)

    # --- Step 5: Subscription tier & report_mode gating ---
    # report_mode is used for:
    # - MyProfile monthly report generation
    # - MyProfile Q&A (compose_response)
    # Fail-closed: if tier cannot be resolved, treat as FREE (light only).
    from subscription import (
        SubscriptionTier,
        MyProfileMode,
        normalize_myprofile_mode,
        is_myprofile_mode_allowed,
        allowed_myprofile_modes_for_tier,
    )
    from subscription_store import get_subscription_tier_for_user

    tier_enum: SubscriptionTier = SubscriptionTier.FREE
    if viewer_user_id:
        try:
            tier_enum = await get_subscription_tier_for_user(
                viewer_user_id,
                default=SubscriptionTier.FREE,
            )
        except Exception as exc:
            logger.warning("Failed to resolve subscription tier; fallback to FREE: %s", exc)
            tier_enum = SubscriptionTier.FREE

    # If client omits report_mode, pick a safe default per tier.
    # - Free: light
    # - Plus/Premium: standard (Deep should be explicitly chosen)
    default_mode = MyProfileMode.LIGHT if tier_enum == SubscriptionTier.FREE else MyProfileMode.STANDARD
    mode_enum = normalize_myprofile_mode(req.report_mode, default=default_mode)

    if not is_myprofile_mode_allowed(tier_enum, mode_enum):
        allowed = [m.value for m in allowed_myprofile_modes_for_tier(tier_enum)]
        raise HTTPException(
            status_code=403,
            detail=f"report_mode '{mode_enum.value}' is not allowed for tier '{tier_enum.value}'. Allowed: {', '.join(allowed)}",
        )

    effective_report_mode: str = mode_enum.value

    target = req.target or "self"
    user_id: Optional[str] = req.user_id

    if target == "external":
        # 外部照会は必ず認証が必要（誰が見ているか、を確定するため）
        if not viewer_user_id:
            raise HTTPException(
                status_code=401,
                detail="Authorization header with Bearer token is required for external MyProfile queries",
            )
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required for external MyProfile queries")

        owner_user_id = str(user_id)
        # 自分の user_id を external で投げてきた場合は self として扱う（UIバグ耐性）
        if owner_user_id == viewer_user_id:
            target = "self"
            user_id = viewer_user_id
        else:
            allowed = await _has_myprofile_link(viewer_user_id=viewer_user_id, owner_user_id=owner_user_id)
            if not allowed:
                raise HTTPException(status_code=403, detail="You are not allowed to query this MyProfile")
            user_id = owner_user_id
    else:
        # self 照会: 認証がある場合は user_id を viewer に固定して、他人の user_id 指定を拒否する。
        if viewer_user_id:
            if user_id and str(user_id) != viewer_user_id:
                raise HTTPException(status_code=403, detail="user_id mismatch")
            user_id = viewer_user_id

    persona_ctx: Optional[Dict[str, Any]] = None
    if user_id:
        # secret の扱い:
        # - self: secret を含めてよい
        # - external: secret を含めない（公開範囲だけで構造傾向を算出）
        include_secret = (target != "external")
        try:
            persona_ctx = build_persona_context_payload(user_id=user_id, include_secret=include_secret)
        except Exception as exc:
            logger.warning("ASTOR persona context build failed: %s", exc)

    # 0) MyProfile（月次自己構造分析レポート）生成
    if is_myprofile_report:
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required for MyProfile report generation")
        include_secret = (target != "external")
        # MyProfile（月次自己構造分析レポート）は「前月（カレンダー月）」を固定で生成する。
        # - UI側の誤設定（例: 28d のローリング）で週次配布のように見える問題を防ぐ。
        # - 配布タイミング（月初）に関係なく、常に “直近の完了済み月（=前月）” を対象にする。
        period = "prev_month"
        prev_text = None
        if include_secret:
            prev_text = await _fetch_latest_monthly_report_text(user_id=str(user_id))
        text, meta2 = build_myprofile_monthly_report(
            user_id=str(user_id),
            period=str(period),
            report_mode=effective_report_mode,
            include_secret=include_secret,
            prev_report_text=prev_text,
        )
        meta: Dict[str, Any] = {"target": target, "engine": "astor_myprofile_report", "version": "1.0.0"}
        meta.update(meta2 or {})
        meta.setdefault("subscription_tier", tier_enum.value)
        meta.setdefault("report_mode", effective_report_mode)
        return InferResponse(output=text, meta=meta)

    # 1) 構造辞書ベースの“定義質問”であれば、そちらを優先して応答
    lang = detect_lang(instr)
    struct_answer = build_structure_answer(instr, lang=lang)
    if struct_answer:
        logger.info("structure_dict hit for instruction=%r", instr[:80])
        return InferResponse(
            output=struct_answer,
            meta={
                "target": target,
                "engine": "structure_dict",
                "version": "1.0.0",
                "subscription_tier": tier_enum.value,
                "report_mode": effective_report_mode,
            },
        )

    # 2) 上記に該当しなければ、従来どおり人格ベースの応答を返す
    output = compose_response(instr, req.input, target, persona_ctx, report_mode=effective_report_mode)

    # Privacy-safe telemetry (no content persisted)
    logger.info("infer called: len=%d target=%s", len(instr), target)

    meta: Dict[str, Any] = {"target": target, "engine": "rule", "version": "1.0.0"}
    meta["subscription_tier"] = tier_enum.value
    meta["report_mode"] = effective_report_mode
    if persona_ctx is not None:
        meta["astor_persona"] = persona_ctx
    return InferResponse(output=output, meta=meta)
# ---------- Entrypoint ----------
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and str(sys.argv[1]).strip().lower() == "rollover":
        raise SystemExit(_run_rollover_cli())

    import uvicorn
    uvicorn.run("app:app", host=HOST, port=PORT, log_level="info")

def detect_lang(text: str) -> str:
    """簡易な言語推定: 日本語(ひらがな/カタカナ/漢字)があれば 'ja'、なければ 'en'。"""
    for ch in text:
        if '\u3040' <= ch <= '\u30ff' or '\u4e00' <= ch <= '\u9fff':
            return 'ja'
    return 'en'
