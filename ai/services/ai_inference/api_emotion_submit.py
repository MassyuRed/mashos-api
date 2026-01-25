# -*- coding: utf-8 -*-
"""
Emotion Submit API for Cocolon
------------------------------
- POST /emotion/submit

役割:
- React Native アプリからの感情入力を受け取る
- Supabase Auth の JWT(Access Token) を検証して user_id を確定する
- Supabase の emotions テーブルに1件保存する
- （将来用）friend_emotion_feed への通知作成の土台を用意しておく

設計メモ:
- 認証:
    - 原則 Authorization: Bearer <access_token> を必須とする
    - access_token は Supabase Auth で発行された JWT を想定
    - 検証は Supabase Auth REST API `/auth/v1/user` を利用する
- Supabase 接続:
    - 以下の環境変数を利用する想定
        - SUPABASE_URL                例: https://xxxx.supabase.co
        - SUPABASE_SERVICE_ROLE_KEY   サービスロールキー
    - Insert 時は service_role で /rest/v1/emotions に書き込む
      （RLSをバイパスしつつ、明示的に user_id を保存する）
- 後方互換:
    - payload.user_id は CURRENT_USER_ID 時代との互換用。基本は使わない。
    - Authorization ヘッダが無い場合に user_id を使ってよいかどうかは
      EMOTION_SUBMIT_ALLOW_LEGACY_USER_ID=true で明示的に有効化する。
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import tempfile
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

# NOTE:
# - Pydantic v2 では "alias" を指定したフィールドに対して、
#   リクエストJSON側がフィールド名（notify_friends）で送ってきた場合、
#   populate_by_name=True を設定しないと値が入らず default が使われる。
# - 本APIはクライアントが notify_friends / send_friend_notification の
#   どちらでも送れるよう後方互換を維持する。
try:
    from pydantic import ConfigDict  # pydantic v2
except ImportError:  # pragma: no cover
    ConfigDict = None  # type: ignore

from astor_core import AstorEngine, AstorRequest, AstorMode, AstorEmotionPayload

logger = logging.getLogger("emotion_submit")

astor_engine = AstorEngine()

# ---------- 環境変数 ----------

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
ALLOW_LEGACY_USER_ID = os.getenv("EMOTION_SUBMIT_ALLOW_LEGACY_USER_ID", "false").lower() in (
    "1",
    "true",
    "yes",
)


# ---------- Push Notifications (FCM) ----------
# Supports:
# - FCM HTTP v1 (recommended): Firebase service account JSON (Admin SDK)
# - (fallback) FCM Legacy HTTP API: Server key (FCM_SERVER_KEY)
#
# Enable/disable:
#   FCM_PUSH_ENABLED=true/false
#
# FCM HTTP v1 credentials (preferred):
#   - FCM_SERVICE_ACCOUNT_FILE=/path/to/serviceAccountKey.json
#     (or GOOGLE_APPLICATION_CREDENTIALS=/path/to/serviceAccountKey.json)
#   - or FCM_SERVICE_ACCOUNT_JSON_BASE64=<base64 of JSON>
#   - or FCM_SERVICE_ACCOUNT_JSON=<raw JSON string>
#
# Legacy fallback (may be unavailable on new Firebase projects):
#   - FCM_SERVER_KEY=AAAA... (Legacy server key)
FCM_PUSH_ENABLED = os.getenv("FCM_PUSH_ENABLED", "true").lower() in ("1", "true", "yes")

# v1 (Admin SDK) credentials
FCM_SERVICE_ACCOUNT_FILE = (os.getenv("FCM_SERVICE_ACCOUNT_FILE") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or "").strip()
FCM_SERVICE_ACCOUNT_JSON_BASE64 = (os.getenv("FCM_SERVICE_ACCOUNT_JSON_BASE64") or "").strip()
FCM_SERVICE_ACCOUNT_JSON = (os.getenv("FCM_SERVICE_ACCOUNT_JSON") or "").strip()

# Legacy
FCM_SERVER_KEY = os.getenv("FCM_SERVER_KEY", "").strip()
FCM_API_URL = (
    (os.getenv("FCM_API_URL", "https://fcm.googleapis.com/fcm/send") or "").strip()
    or "https://fcm.googleapis.com/fcm/send"
)
try:
    FCM_TIMEOUT_SEC = float(os.getenv("FCM_TIMEOUT_SEC", "5.0"))
except ValueError:
    FCM_TIMEOUT_SEC = 5.0

# Firebase Admin init state (for v1)
_FCM_APP_INITIALIZED = False
_FCM_APP_INIT_LOCK = threading.Lock()
_FCM_SERVICE_ACCOUNT_TMPFILE: Optional[str] = None
_FCM_V1_APP_NAME = os.getenv("FCM_V1_APP_NAME", "cocolon_fcm_v1").strip() or "cocolon_fcm_v1"
_FCM_V1_APP: Optional[Any] = None  # firebase_admin.App



def _has_fcm_v1_credentials() -> bool:
    """FCM HTTP v1 の資格情報が設定されているかをざっくり判定する。"""
    if FCM_SERVICE_ACCOUNT_FILE and os.path.isfile(FCM_SERVICE_ACCOUNT_FILE):
        return True
    if FCM_SERVICE_ACCOUNT_JSON_BASE64:
        return True
    if FCM_SERVICE_ACCOUNT_JSON:
        return True
    return False


def _ensure_fcm_service_account_file() -> str:
    """サービスアカウントJSONをファイルパスとして確保する。

    優先順位:
      1) FCM_SERVICE_ACCOUNT_FILE / GOOGLE_APPLICATION_CREDENTIALS の実ファイル
      2) FCM_SERVICE_ACCOUNT_JSON_BASE64 / FCM_SERVICE_ACCOUNT_JSON を /tmp に書き出して利用
    """
    global _FCM_SERVICE_ACCOUNT_TMPFILE

    if FCM_SERVICE_ACCOUNT_FILE and os.path.isfile(FCM_SERVICE_ACCOUNT_FILE):
        return FCM_SERVICE_ACCOUNT_FILE

    if _FCM_SERVICE_ACCOUNT_TMPFILE and os.path.isfile(_FCM_SERVICE_ACCOUNT_TMPFILE):
        return _FCM_SERVICE_ACCOUNT_TMPFILE

    raw_json: Optional[str] = None
    if FCM_SERVICE_ACCOUNT_JSON_BASE64:
        try:
            raw_json = base64.b64decode(FCM_SERVICE_ACCOUNT_JSON_BASE64).decode("utf-8")
        except Exception as exc:
            logger.error("Failed to decode FCM_SERVICE_ACCOUNT_JSON_BASE64: %s", exc)
            raw_json = None
    elif FCM_SERVICE_ACCOUNT_JSON:
        raw_json = FCM_SERVICE_ACCOUNT_JSON

    if not raw_json:
        return ""

    try:
        info = json.loads(raw_json)
    except Exception as exc:
        logger.error("Invalid FCM service account JSON: %s", exc)
        return ""

    # NOTE: firebase_admin.credentials.Certificate() はファイルパスを最も確実に扱えるため、
    #       env に JSON 文字列で渡された場合は /tmp に書き出して利用する。
    try:
        fd, path = tempfile.mkstemp(prefix="firebase_service_account_", suffix=".json")
        os.close(fd)
        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps(info))
        try:
            os.chmod(path, 0o600)
        except Exception:
            pass

        _FCM_SERVICE_ACCOUNT_TMPFILE = path
        return path
    except Exception as exc:
        logger.error("Failed to write service account JSON to tmp file: %s", exc)
        return ""


def _ensure_firebase_admin_initialized() -> bool:
    """Firebase Admin SDK を初期化する（FCM HTTP v1 用）。

    重要:
    - 既に default app がどこかで初期化されていても、それを信用しない。
      Render 環境では ADC(デフォルト認証) が使えず 401 になりやすいため、
      必ず service account credential で named app を用意して送信時にそれを使う。
    """
    global _FCM_APP_INITIALIZED, _FCM_V1_APP

    if _FCM_APP_INITIALIZED and _FCM_V1_APP is not None:
        return True

    with _FCM_APP_INIT_LOCK:
        if _FCM_APP_INITIALIZED and _FCM_V1_APP is not None:
            return True

        try:
            import firebase_admin
            from firebase_admin import credentials
        except Exception as exc:
            logger.error("firebase-admin is not available: %s", exc)
            return False

        # 既に named app があればそれを使う
        try:
            _FCM_V1_APP = firebase_admin.get_app(_FCM_V1_APP_NAME)
            _FCM_APP_INITIALIZED = True
            logger.info(
                "Firebase Admin SDK initialized for FCM push (v1) [patch_v4 name=%s existing].",
                _FCM_V1_APP_NAME,
            )
            return True
        except Exception:
            _FCM_V1_APP = None

        # credential を service account から必ず用意
        cred_path = _ensure_fcm_service_account_file()
        if not cred_path:
            # Render Secret Files の標準パスも念のため見る
            default_path = "/etc/secrets/firebase_service_account.json"
            if os.path.isfile(default_path):
                cred_path = default_path
            else:
                return False

        try:
            cred = credentials.Certificate(cred_path)
            _FCM_V1_APP = firebase_admin.initialize_app(cred, name=_FCM_V1_APP_NAME)
            _FCM_APP_INITIALIZED = True
            logger.info(
                "Firebase Admin SDK initialized for FCM push (v1) [patch_v4 name=%s].",
                _FCM_V1_APP_NAME,
            )
            return True
        except Exception as exc:
            logger.error("Failed to initialize Firebase Admin SDK: %s", exc)
            _FCM_V1_APP = None
            return False


# 強度ラベル（RN側の表示と合わせる）
STRENGTH_LABEL_JA: Dict[str, str] = {"weak": "弱", "medium": "中", "strong": "強"}
# 強度スコア（structure_engine/extract.py と同じ定義）
STRENGTH_SCORE: Dict[str, float] = {"weak": 1.0, "medium": 2.0, "strong": 3.0}


def _ensure_supabase_config() -> None:
    """Supabase 接続情報が無い場合は 500 を返す。"""
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        logger.error("Supabase configuration missing: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY is not set")
        raise HTTPException(status_code=500, detail="Supabase configuration is missing")


def _extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    """Authorization ヘッダから Bearer トークンを取り出す。"""
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer" and parts[1]:
        return parts[1]
    return None


async def _resolve_user_id_from_token(access_token: str) -> str:
    """
    Supabase Auth の `/auth/v1/user` を利用して JWT を検証しつつ user_id を取得する。
    - 200 以外の場合は 401 を返す。
    """
    _ensure_supabase_config()
    url = f"{SUPABASE_URL}/auth/v1/user"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
    }

    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(url, headers=headers)

    if resp.status_code != 200:
        logger.warning(
            "Supabase /auth/v1/user failed: status=%s body=%s",
            resp.status_code,
            resp.text[:2000],
        )
        raise HTTPException(status_code=401, detail="Invalid or expired access token")

    data = resp.json()
    user_id = data.get("id")
    if not user_id:
        logger.error("Supabase /auth/v1/user returned no id field")
        raise HTTPException(status_code=401, detail="Failed to resolve user from token")

    return str(user_id)


@dataclass
class NormalizedEmotion:
    type: str
    strength: str  # "weak" | "medium" | "strong"


def _normalize_emotions(
    raw: Sequence[Union["EmotionItem", str]],
) -> Tuple[List[str], List[Dict[str, Any]], Optional[float]]:
    """
    emotions 配列を正規化する。
    - 入力は EmotionItem または str の混在を許容する（後方互換用）。
    - 出力:
        - emotions_tags: ["喜び", "不安", ...] といった文字列配列
        - emotion_details: [{type, strength}, ...] の配列（JSONBに保存）
        - avg_strength: 強度スコア(1..3)の平均（None もあり得る）
    """
    normalized: List[NormalizedEmotion] = []

    for item in raw:
        if isinstance(item, EmotionItem):
            t = (item.type or "").strip()
            s = (item.strength or "medium").lower()
        else:
            # 旧: string[] の場合は "medium" とみなす
            t = str(item).strip()
            s = "medium"

        if not t:
            # 空文字はスキップ
            continue

        if s not in STRENGTH_SCORE:
            s = "medium"

        normalized.append(NormalizedEmotion(type=t, strength=s))

    if not normalized:
        return [], [], None

    tags = [n.type for n in normalized]
    details = [asdict(n) for n in normalized]
    scores = [STRENGTH_SCORE.get(n.strength, 2.0) for n in normalized]
    avg_strength = sum(scores) / len(scores) if scores else None
    return tags, details, avg_strength


async def _insert_emotion_row(
    *,
    user_id: str,
    emotions: List[str],
    emotion_details: List[Dict[str, Any]],
    emotion_strength_avg: Optional[float],
    memo: Optional[str],
    created_at: str,
    is_secret: bool,
) -> Dict[str, Any]:
    """
    Supabase の emotions テーブルに1件INSERTする。
    - Prefer: return=representation で挿入された行をそのまま返す。
    """
    _ensure_supabase_config()
    url = f"{SUPABASE_URL}/rest/v1/emotions"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

    payload: Dict[str, Any] = {
        "user_id": user_id,
        "emotions": emotions,
        "memo": memo,
        "created_at": created_at,
        "is_secret": bool(is_secret),
    }
    if emotion_details:
        payload["emotion_details"] = emotion_details
    if emotion_strength_avg is not None:
        payload["emotion_strength_avg"] = emotion_strength_avg

    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.post(url, headers=headers, json=payload)

    if resp.status_code not in (200, 201):
        logger.error(
            "Supabase insert into emotions failed: status=%s body=%s",
            resp.status_code,
            resp.text[:2000],
        )
        raise HTTPException(status_code=502, detail="Failed to save emotion log")

    try:
        data = resp.json()
    except ValueError:
        logger.warning("Supabase response is not JSON; returning minimal info")
        return {"id": None, "created_at": created_at}

    if isinstance(data, list) and data:
        return data[0]
    if isinstance(data, dict):
        return data
    return {"id": None, "created_at": created_at}



# ---------- MyProfile Latest Report (auto-refresh) ----------
# 目的:
# - ユーザーが感情入力した直後に、MyProfile の「最新版プレビュー」を更新しておく。
# - 既存UI（Supabase の myprofile_reports を読むだけ）でも最新が反映されるようにする。
#
# 注意:
# - 失敗しても emotion/submit 自体は成功として扱う（入力保存を優先）。
#
# Env (optional):
# - MYPROFILE_LATEST_AUTO_REFRESH_ENABLED=true/false
# - MYPROFILE_LATEST_REFRESH_MIN_INTERVAL_SECONDS=90
# - MYPROFILE_LATEST_PERIOD=28d  (例: 7d / 28d / 30d)
#
# 既存アプリ実装と互換のため、latest は period_start/end を固定値にして 1 行を使い回す。
LATEST_REPORT_PERIOD_START = "1970-01-01T00:00:00.000Z"
LATEST_REPORT_PERIOD_END = "1970-01-01T00:00:00.000Z"

def _env_truthy(name: str, default: str = "true") -> bool:
    v = os.getenv(name, default)
    return str(v).strip().lower() in ("1", "true", "yes", "y", "on")

MYPROFILE_LATEST_AUTO_REFRESH_ENABLED = _env_truthy(
    "MYPROFILE_LATEST_AUTO_REFRESH_ENABLED", "true"
)

try:
    MYPROFILE_LATEST_REFRESH_MIN_INTERVAL_SECONDS = int(
        os.getenv("MYPROFILE_LATEST_REFRESH_MIN_INTERVAL_SECONDS", "90")
    )
except Exception:
    MYPROFILE_LATEST_REFRESH_MIN_INTERVAL_SECONDS = 90

MYPROFILE_LATEST_PERIOD = str(os.getenv("MYPROFILE_LATEST_PERIOD", "28d") or "28d").strip()

async def _fetch_myprofile_latest_generated_at(user_id: str) -> Optional[str]:
    """myprofile_reports(latest) の generated_at を取得する（無ければ None）。"""
    _ensure_supabase_config()

    url = f"{SUPABASE_URL}/rest/v1/myprofile_reports"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }
    params = {
        "select": "generated_at",
        "user_id": f"eq.{user_id}",
        "report_type": "eq.latest",
        "period_start": f"eq.{LATEST_REPORT_PERIOD_START}",
        "period_end": f"eq.{LATEST_REPORT_PERIOD_END}",
        "limit": "1",
    }

    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(url, headers=headers, params=params)

    # 200: OK, 206: Partial Content（range）
    if resp.status_code not in (200, 206):
        logger.warning(
            "Supabase fetch myprofile_reports(latest) failed: status=%s body=%s",
            resp.status_code,
            resp.text[:800],
        )
        return None

    try:
        data = resp.json()
    except Exception:
        return None

    if isinstance(data, list) and data:
        return data[0].get("generated_at")
    if isinstance(data, dict):
        return data.get("generated_at")
    return None

async def _upsert_myprofile_latest_report_row(payload: Dict[str, Any]) -> None:
    """myprofile_reports に latest を upsert（失敗したら例外）。"""
    _ensure_supabase_config()

    url = f"{SUPABASE_URL}/rest/v1/myprofile_reports"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        # merge duplicates on conflict
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }
    params = {
        "on_conflict": "user_id,report_type,period_start,period_end",
    }

    async with httpx.AsyncClient(timeout=8.0) as client:
        resp = await client.post(url, headers=headers, params=params, json=payload)

    if resp.status_code not in (200, 201, 204):
        raise RuntimeError(
            f"Supabase upsert myprofile_reports(latest) failed: HTTP {resp.status_code} {resp.text[:800]}"
        )

async def _auto_refresh_myprofile_latest_report(user_id: str) -> None:
    """感情入力後に MyProfile 最新レポート（プレビュー）を更新する。"""
    if not MYPROFILE_LATEST_AUTO_REFRESH_ENABLED:
        return

    uid = str(user_id or "").strip()
    if not uid:
        return

    # ---- throttle ----
    min_interval = int(MYPROFILE_LATEST_REFRESH_MIN_INTERVAL_SECONDS or 0)
    if min_interval > 0:
        try:
            last_iso = await _fetch_myprofile_latest_generated_at(uid)
            if last_iso:
                try:
                    last_dt = datetime.fromisoformat(last_iso.replace("Z", "+00:00"))
                    now_dt = datetime.now(timezone.utc)
                    if (now_dt - last_dt).total_seconds() < float(min_interval):
                        return
                except Exception:
                    # 解析できない場合は更新を続行
                    pass
        except Exception:
            # 取得できなくても更新は続行
            pass

    # ---- determine report_mode (fail-closed) ----
    report_mode = "light"
    try:
        from subscription_store import get_subscription_tier_for_user
        from subscription import SubscriptionTier

        tier = await get_subscription_tier_for_user(uid, default=SubscriptionTier.FREE)
        report_mode = "light" if tier == SubscriptionTier.FREE else "standard"
    except Exception:
        report_mode = "light"

    # ---- Phase10: generation lock (best-effort) ----
    lock_key = None
    lock_owner = None
    lock_acquired = True
    try:
        from generation_lock import build_lock_key, make_owner_id, release_lock, try_acquire_lock

        lock_key = build_lock_key(
            namespace="myprofile",
            user_id=uid,
            report_type="latest",
            period_start=LATEST_REPORT_PERIOD_START,
            period_end=LATEST_REPORT_PERIOD_END,
        )
        lock_owner = make_owner_id("auto_refresh_latest")
        ttl = int(os.getenv("GENERATION_LOCK_TTL_SECONDS_MYPROFILE_LATEST", "180") or "180")
        lr = await try_acquire_lock(
            lock_key=lock_key,
            ttl_seconds=ttl,
            owner_id=lock_owner,
            context={
                "namespace": "myprofile",
                "user_id": uid,
                "report_type": "latest",
                "period": MYPROFILE_LATEST_PERIOD,
                "report_mode": report_mode,
                "source": "auto_refresh_emotion_submit",
            },
        )
        lock_acquired = bool(getattr(lr, "acquired", False))
        lock_owner = getattr(lr, "owner_id", lock_owner)
    except Exception:
        lock_acquired = True

    if not lock_acquired:
        # Someone else is generating; skip silently.
        return

    # ---- generate latest text (rule-based; no LLM) ----
    try:
        from astor_myprofile_report import build_myprofile_monthly_report

        now_dt = datetime.now(timezone.utc).replace(microsecond=0)
        text, meta = build_myprofile_monthly_report(
            user_id=uid,
            period=MYPROFILE_LATEST_PERIOD or "28d",
            report_mode=report_mode,
            include_secret=True,
            now=now_dt,
            prev_report_text=None,
        )
    except Exception as exc:
        raise RuntimeError(f"latest report build failed: {exc}") from exc

    text = str(text or "").strip()
    if not text:
        return

    # snapshot window (for debugging / UI hints)
    try:
        days = 28
        try:
            # reuse astor_myprofile_report's parser if available
            from astor_myprofile_report import parse_period_days
            days = int(parse_period_days(MYPROFILE_LATEST_PERIOD))
        except Exception:
            pass
        end_dt = datetime.now(timezone.utc).replace(microsecond=0)
        start_dt = end_dt - timedelta(days=max(days, 1))
        snap = {
            "start": start_dt.isoformat().replace("+00:00", "Z"),
            "end": end_dt.isoformat().replace("+00:00", "Z"),
            "period": MYPROFILE_LATEST_PERIOD,
        }
    except Exception:
        snap = {"period": MYPROFILE_LATEST_PERIOD}

    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    payload = {
        "user_id": uid,
        "report_type": "latest",
        "period_start": LATEST_REPORT_PERIOD_START,
        "period_end": LATEST_REPORT_PERIOD_END,
        "title": "自己構造レポート（最新版）",
        "content_text": text,
        "content_json": {
            **(meta or {}),
            "source": "auto_refresh_emotion_submit",
            "snapshot": snap,
            "generated_at_server": generated_at,
        },
        "generated_at": generated_at,
    }

    try:
        await _upsert_myprofile_latest_report_row(payload)
    finally:
        try:
            from generation_lock import release_lock

            if lock_key:
                await release_lock(lock_key=lock_key, owner_id=lock_owner)
        except Exception:
            pass


# ---------- Pydantic models ----------


class EmotionItem(BaseModel):
    type: str = Field(..., description="感情タグ（例: '喜び', '不安' など）")
    strength: str = Field(..., description="強度（weak / medium / strong 想定）")


class EmotionSubmitRequest(BaseModel):
    user_id: Optional[str] = Field(
        default=None,
        description="後方互換用。原則としてサーバー側では JWT から user_id を確定する。",
    )
    emotions: List[Union[EmotionItem, str]] = Field(
        ...,
        description="感情＋強度の配列。旧形式 string[] も許容する。",
    )
    memo: Optional[str] = Field(default=None, description="メモ本文")
    created_at: Optional[str] = Field(
        default=None,
        description="ISO8601文字列。未指定時はサーバー側で now() を採用。",
    )
    is_secret: Optional[bool] = Field(
        default=False,
        description="MyModel external からの照会制御用フラグ（Frend通知には影響しない）。",
    )

    notify_friends: Optional[bool] = Field(
        default=True,
        alias="send_friend_notification",
        description=(
            "フレンドに通知を送るかどうか。true のとき friend_emotion_feed と Push 通知を作成する。"
            "後方互換のため未指定は true。"
        ),
    )

    # Pydantic v2: alias を指定したフィールドでも、
    # フィールド名（notify_friends）での入力を許可する。
    # （Config.allow_population_by_field_name は v1 用）
    if ConfigDict is not None:  # pragma: no cover
        model_config = ConfigDict(populate_by_name=True)
    else:  # pragma: no cover
        class Config:
            # payload に notify_friends / send_friend_notification のどちらが来ても受け取れるようにする
            allow_population_by_field_name = True


class EmotionSubmitResponse(BaseModel):
    status: str = Field(..., description="'ok' 固定（現状）")
    id: Optional[Any] = Field(default=None, description="保存された emotions.id（あれば）")
    created_at: str = Field(..., description="保存時刻（ISO8601）")



async def _fetch_friend_viewer_ids(user_id: str) -> List[str]:
    """friendships テーブルから、指定ユーザーのフレンド（通知の配布先）を取得する。

    前提:
    - friendships は (user_id, friend_user_id) の行で表現する。
    - 実装上は「双方向2行」を作る運用が最もシンプルだが、
      片方向しか入っていない場合にも耐えるため、両方向を問い合わせて set で統合する。
    """
    _ensure_supabase_config()
    if not user_id:
        return []

    url = f"{SUPABASE_URL}/rest/v1/friendships"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    }

    viewer_ids_set = set()

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # 自分が user_id 側の行（標準運用：ここだけで十分）
            resp1 = await client.get(
                url,
                headers=headers,
                params={
                    "select": "user_id,friend_user_id",
                    "user_id": f"eq.{user_id}",
                },
            )
            if resp1.status_code < 300:
                rows1 = resp1.json()
                if isinstance(rows1, list):
                    for row in rows1:
                        fid = row.get("friend_user_id")
                        if isinstance(fid, str) and fid and fid != user_id:
                            viewer_ids_set.add(fid)
            else:
                logger.error(
                    "Supabase select from friendships (user_id side) failed: status=%s body=%s",
                    resp1.status_code,
                    resp1.text[:2000],
                )

            # 自分が friend_user_id 側の行（片方向しか存在しないケースの救済）
            resp2 = await client.get(
                url,
                headers=headers,
                params={
                    "select": "user_id,friend_user_id",
                    "friend_user_id": f"eq.{user_id}",
                },
            )
            if resp2.status_code < 300:
                rows2 = resp2.json()
                if isinstance(rows2, list):
                    for row in rows2:
                        uid = row.get("user_id")
                        if isinstance(uid, str) and uid and uid != user_id:
                            viewer_ids_set.add(uid)
            else:
                logger.error(
                    "Supabase select from friendships (friend_user_id side) failed: status=%s body=%s",
                    resp2.status_code,
                    resp2.text[:2000],
                )
    except Exception as exc:
        logger.error("Failed to fetch friendships for user %s: %s", user_id, exc)

    return list(viewer_ids_set)


async def _fetch_profile_display_name(user_id: str) -> str:
    """profiles テーブルから display_name を取得する。レコードが無い場合は 'Friend' を返す。"""
    _ensure_supabase_config()
    if not user_id:
        return "Friend"

    url = f"{SUPABASE_URL}/rest/v1/profiles"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    }
    params = {
        "select": "display_name",
        "id": f"eq.{user_id}",
        "limit": 1,
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, headers=headers, params=params)
        if resp.status_code >= 300:
            logger.error(
                "Supabase select from profiles failed: status=%s body=%s",
                resp.status_code,
                resp.text[:2000],
            )
            return "Friend"

        rows = resp.json()
        if isinstance(rows, list) and rows:
            display_name = rows[0].get("display_name")
            if isinstance(display_name, str) and display_name.strip():
                return display_name.strip()
    except Exception as exc:
        logger.error("Failed to fetch profile for user %s: %s", user_id, exc)

    return "Friend"



def _is_fcm_enabled() -> bool:
    """FCM Push が有効かどうか（環境変数で制御）。"""
    if not FCM_PUSH_ENABLED:
        return False
    if _has_fcm_v1_credentials():
        return True
    return bool(FCM_SERVER_KEY)



def _format_emotion_push_body(emotion_details: List[Dict[str, Any]]) -> str:
    """通知本文用に感情配列を短い文字列に整形する。"""
    parts: List[str] = []
    for it in emotion_details or []:
        if not isinstance(it, dict):
            continue
        t = str(it.get("type") or "").strip()
        s = str(it.get("strength") or "").lower().strip()
        if not t:
            continue
        label = STRENGTH_LABEL_JA.get(s, "")
        parts.append(f"『{t}{f' {label}' if label else ''}』")

    if not parts:
        return ""

    # 例: 『喜び 強』  『不安 弱』
    body = "  ".join(parts)
    return body[:180]


async def _fetch_push_tokens_for_users(user_ids: List[str]) -> Dict[str, str]:
    """profiles から push_token を取得する（service_roleでRLSをバイパス）。

    - push_enabled=false のユーザーは除外する（列が無い場合は全員ON扱いで後方互換）。
    """
    _ensure_supabase_config()
    ids = [uid for uid in (user_ids or []) if isinstance(uid, str) and uid.strip()]
    if not ids:
        return {}

    url = f"{SUPABASE_URL}/rest/v1/profiles"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    }

    # PostgREST: id=in.("uuid1","uuid2",...)
    quoted = ",".join([f"\"{uid}\"" for uid in ids])

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # まずは push_enabled も含めて取得（通知OFFを除外するため）
            params = {
                "select": "id,push_token,push_enabled",
                "id": f"in.({quoted})",
            }
            resp = await client.get(url, headers=headers, params=params)

            use_push_enabled = resp.status_code < 300
            if resp.status_code >= 300:
                # push_enabled 列が無い等でもここに来るので、後方互換で push_token のみにフォールバック
                logger.warning(
                    "Supabase select id,push_token,push_enabled from profiles failed (fallback to push_token only): status=%s body=%s",
                    resp.status_code,
                    resp.text[:2000],
                )
                params = {
                    "select": "id,push_token",
                    "id": f"in.({quoted})",
                }
                resp = await client.get(url, headers=headers, params=params)

        if resp.status_code >= 300:
            # push_token 列が無い等でもここに来るので、warn に留める
            logger.warning(
                "Supabase select push_token from profiles failed: status=%s body=%s",
                resp.status_code,
                resp.text[:2000],
            )
            return {}

        rows = resp.json()
        out: Dict[str, str] = {}
        if isinstance(rows, list):
            for row in rows:
                if not isinstance(row, dict):
                    continue
                uid = row.get("id")
                token = row.get("push_token")

                if use_push_enabled:
                    enabled = row.get("push_enabled")
                    if enabled is False:
                        continue

                if isinstance(uid, str) and isinstance(token, str) and token.strip():
                    out[uid] = token.strip()
        return out
    except Exception as exc:
        logger.error("Failed to fetch push tokens: %s", exc)
        return {}


def _chunk_list(xs: List[str], size: int) -> List[List[str]]:
    if size <= 0:
        return [xs]
    return [xs[i : i + size] for i in range(0, len(xs), size)]



# ---- FCM HTTP v1 (Direct HTTP + OAuth2) [patch_v5] ----
# firebase_admin 経由で 401 ("missing required authentication credential") が継続するケースがあるため、
# Render Shell で成功した「service account -> OAuth access token -> HTTP v1」方式に寄せる。
_FCM_OAUTH_TOKEN: Optional[str] = None
_FCM_OAUTH_EXPIRY: Optional[datetime] = None
_FCM_OAUTH_PROJECT_ID: Optional[str] = None
_FCM_OAUTH_CLIENT_EMAIL: Optional[str] = None
_FCM_OAUTH_LOCK = threading.Lock()


def _get_fcm_oauth_access_token() -> Tuple[str, datetime, str, str]:
    """FCM HTTP v1 用の OAuth2 access token を取得/キャッシュして返す。

    戻り値: (token, expiry, project_id, client_email)
    """
    global _FCM_OAUTH_TOKEN, _FCM_OAUTH_EXPIRY, _FCM_OAUTH_PROJECT_ID, _FCM_OAUTH_CLIENT_EMAIL

    with _FCM_OAUTH_LOCK:
        now = datetime.now(timezone.utc)
        if _FCM_OAUTH_TOKEN and _FCM_OAUTH_EXPIRY and (_FCM_OAUTH_EXPIRY - now) > timedelta(seconds=60):
            return (
                _FCM_OAUTH_TOKEN,
                _FCM_OAUTH_EXPIRY,
                _FCM_OAUTH_PROJECT_ID or "",
                _FCM_OAUTH_CLIENT_EMAIL or "",
            )

        # まずは既存の設定から探す（/etc/secrets を最後の砦として見る）
        cred_path = _ensure_fcm_service_account_file()
        if not cred_path:
            default_path = "/etc/secrets/firebase_service_account.json"
            if os.path.isfile(default_path):
                cred_path = default_path
            else:
                raise RuntimeError("FCM service account file not found.")

        project_id = ""
        client_email = ""
        try:
            with open(cred_path, "r", encoding="utf-8") as f:
                info = json.load(f)
            project_id = str(info.get("project_id") or "")
            client_email = str(info.get("client_email") or "")
        except Exception:
            # JSON が読めなくても Credentials 側から拾えることがあるので続行
            project_id = ""
            client_email = ""

        try:
            from google.oauth2 import service_account
        except Exception as exc:
            raise RuntimeError(f"google-auth is not available: {exc}")

        scopes = ["https://www.googleapis.com/auth/firebase.messaging"]
        creds = service_account.Credentials.from_service_account_file(cred_path, scopes=scopes)

        # refresh (requests が無い環境もあり得るので transport をフォールバック)
        req = None
        try:
            from google.auth.transport.requests import Request as GARequest  # type: ignore
            req = GARequest()
        except Exception:
            try:
                from google.auth.transport.urllib3 import Request as GARequest  # type: ignore
                req = GARequest()
            except Exception as exc:
                raise RuntimeError(f"google-auth transport is not available: {exc}")

        creds.refresh(req)
        token = getattr(creds, "token", None)
        expiry = getattr(creds, "expiry", None)

        if not token or not expiry:
            raise RuntimeError("Failed to mint OAuth access token for FCM v1.")

        if getattr(expiry, "tzinfo", None) is None:
            expiry = expiry.replace(tzinfo=timezone.utc)

        if not project_id:
            project_id = getattr(creds, "project_id", "") or ""

        _FCM_OAUTH_TOKEN = str(token)
        _FCM_OAUTH_EXPIRY = expiry
        _FCM_OAUTH_PROJECT_ID = project_id
        _FCM_OAUTH_CLIENT_EMAIL = client_email

        logger.info(
            "FCM v1 OAuth token refreshed [patch_v5]: project_id=%s token_len=%s exp=%s sa=%s",
            project_id,
            len(_FCM_OAUTH_TOKEN),
            _FCM_OAUTH_EXPIRY.isoformat(),
            (client_email or ""),
        )

        return _FCM_OAUTH_TOKEN, _FCM_OAUTH_EXPIRY, project_id, client_email


async def _send_fcm_push_v1(
    *,
    tokens: List[str],
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
) -> None:
    """FCM HTTP v1 (Direct HTTP + OAuth2) で push を送る（best-effort）。

    - service account JSON から OAuth2 access token を作り、HTTP v1 に投げる。
    - 401 が出たらトークンを作り直して 1回だけリトライする。
    """
    if not FCM_PUSH_ENABLED:
        return

    # credentials が設定されていなくても /etc/secrets にあれば送る
    if not (_has_fcm_v1_credentials() or os.path.isfile("/etc/secrets/firebase_service_account.json")):
        return

    # 重複除去・空除去
    uniq: List[str] = []
    seen = set()
    for t in tokens or []:
        if not isinstance(t, str):
            continue
        tt = t.strip()
        if not tt or tt in seen:
            continue
        seen.add(tt)
        uniq.append(tt)

    if not uniq:
        return

    # FCM data payload は string:string が必要
    data_str: Dict[str, str] = {}
    if data:
        for k, v in data.items():
            if k is None or v is None:
                continue
            data_str[str(k)] = str(v)

    # token / project を取得
    try:
        access_token, expiry, project_id, client_email = _get_fcm_oauth_access_token()
    except Exception as exc:
        logger.error("FCM v1 OAuth token error [patch_v5]: %s", exc)
        return

    if not project_id:
        logger.error("FCM v1 project_id is empty [patch_v5].")
        return

    url = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; UTF-8",
    }

    async def _post_one(tok: str, *, retry_on_401: bool = True) -> Tuple[bool, int, str]:
        message: Dict[str, Any] = {
            "token": tok,
            "notification": {"title": title, "body": body},
            "android": {"priority": "HIGH"},
            "apns": {
                "headers": {
                    "apns-push-type": "alert",
                    "apns-priority": "10",
                },
                "payload": {
                    "aps": {
                        "sound": "default",
                    }
                },
            },
        }
        if data_str:
            message["data"] = data_str

        payload: Dict[str, Any] = {"message": message}

        async with httpx.AsyncClient(timeout=FCM_TIMEOUT_SEC) as client:
            resp = await client.post(url, headers=headers, json=payload)

        if resp.status_code == 200:
            return True, resp.status_code, ""

        # 401 の場合は token を作り直して 1回だけリトライ
        if retry_on_401 and resp.status_code == 401:
            global _FCM_OAUTH_TOKEN, _FCM_OAUTH_EXPIRY
            with _FCM_OAUTH_LOCK:
                _FCM_OAUTH_TOKEN = None
                _FCM_OAUTH_EXPIRY = None
            try:
                new_token, _, _, _ = _get_fcm_oauth_access_token()
                headers["Authorization"] = f"Bearer {new_token}"
            except Exception as exc:
                return False, resp.status_code, f"retry token refresh failed: {exc}"

            async with httpx.AsyncClient(timeout=FCM_TIMEOUT_SEC) as client:
                resp2 = await client.post(url, headers=headers, json=payload)

            if resp2.status_code == 200:
                return True, resp2.status_code, ""
            return False, resp2.status_code, (resp2.text or "")[:600]

        return False, resp.status_code, (resp.text or "")[:600]

    success = 0
    failure = 0
    errs: List[str] = []

    for tok in uniq:
        try:
            ok, status, err = await _post_one(tok)
            if ok:
                success += 1
            else:
                failure += 1
                errs.append(f"status={status} err={err}")
        except Exception as exc:
            failure += 1
            errs.append(str(exc))

    logger.info("FCM v1 push sent [patch_v5]: success=%s failure=%s", success, failure)
    if failure and errs:
        logger.warning("FCM v1 push failures (sample) [patch_v5 told=%s sa=%s]: %s", project_id, (client_email or ""), errs[:3])

async def _send_fcm_push_legacy(
    *,
    tokens: List[str],
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
) -> None:
    """FCM Legacy API で push を送る（best-effort）。"""
    if not (FCM_PUSH_ENABLED and FCM_SERVER_KEY):
        return

    # 重複除去・空除去
    uniq: List[str] = []
    seen = set()
    for t in tokens or []:
        if not isinstance(t, str):
            continue
        tt = t.strip()
        if not tt or tt in seen:
            continue
        seen.add(tt)
        uniq.append(tt)

    if not uniq:
        return

    headers = {
        "Authorization": f"key={FCM_SERVER_KEY}",
        "Content-Type": "application/json",
    }

    # Legacy API は registration_ids で最大1000件まで送れる（安全側で900に分割）
    batches = _chunk_list(uniq, 900)

    async with httpx.AsyncClient(timeout=FCM_TIMEOUT_SEC) as client:
        for batch in batches:
            payload: Dict[str, Any] = {
                "registration_ids": batch,
                "priority": "high",
                "notification": {"title": title, "body": body, "sound": "default"},
            }
            if data:
                payload["data"] = data

            resp = await client.post(FCM_API_URL, headers=headers, json=payload)
            if resp.status_code != 200:
                logger.error(
                    "FCM legacy push send failed: status=%s body=%s",
                    resp.status_code,
                    resp.text[:2000],
                )
                continue

            try:
                js = resp.json()
            except Exception:
                js = None

            if isinstance(js, dict):
                success = js.get("success")
                failure = js.get("failure")
                logger.info("FCM legacy push sent: success=%s failure=%s", success, failure)

                if failure:
                    results = js.get("results")
                    if isinstance(results, list):
                        errs = [r.get("error") for r in results if isinstance(r, dict) and r.get("error")]
                        if errs:
                            logger.warning("FCM legacy push failures (sample): %s", errs[:5])


async def _send_fcm_push(
    *,
    tokens: List[str],
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
) -> None:
    """FCM Push を送る（best-effort）。

    優先順位:
      1) FCM HTTP v1 (service account) が設定されていれば v1 で送る
      2) それ以外は Legacy (FCM_SERVER_KEY) があれば送る
    """
    if not _is_fcm_enabled():
        return

    if _has_fcm_v1_credentials():
        await _send_fcm_push_v1(tokens=tokens, title=title, body=body, data=data)
        return

    await _send_fcm_push_legacy(tokens=tokens, title=title, body=body, data=data)

async def _push_notify_friends_about_emotion(
    *,
    viewer_user_ids: List[str],
    owner_user_id: str,
    owner_name: str,
    emotion_details: List[Dict[str, Any]],
    created_at: str,
) -> None:
    """フレンド向けに Push 通知を送る（FCM）。"""
    if not _is_fcm_enabled():
        return

    token_map = await _fetch_push_tokens_for_users(viewer_user_ids)
    tokens = list(token_map.values())
    if not tokens:
        return

    # 仕様: 通知で飛ばす内容は「誰が + 感情選択内容」。
    emotion_body = _format_emotion_push_body(emotion_details)
    if not emotion_body:
        return

    owner_label = (owner_name or "").strip() or "フレンド"
    if owner_label == "Friend":
        owner_label = "フレンド"
    body = f"{owner_label}さんが{emotion_body}を入力しました"

    # iOS は notification.body が空だと通知が表示されない/抑制されるケースがあるため、
    # 本文(body)に「誰が + 感情選択内容」を入れる。
    await _send_fcm_push(tokens=tokens, title="Cocolon", body=body, data=None)

async def _insert_friend_emotion_feed_rows(
    *,
    viewer_user_ids: List[str],
    owner_user_id: str,
    owner_name: str,
    items: List[Dict[str, Any]],
    created_at: str,
) -> None:
    """Supabase の friend_emotion_feed テーブルに通知レコードを複数件INSERTする。"""
    _ensure_supabase_config()
    if not viewer_user_ids:
        return
    if not items:
        # items が空配列の場合は通知をスキップ
        return

    url = f"{SUPABASE_URL}/rest/v1/friend_emotion_feed"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    payload = [
        {
            "viewer_user_id": vid,
            "owner_user_id": owner_user_id,
            "owner_name": owner_name,
            "items": items,
            "created_at": created_at,
        }
        for vid in viewer_user_ids
        if vid and vid != owner_user_id
    ]
    if not payload:
        return

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code not in (200, 201, 204):
            logger.error(
                "Supabase insert into friend_emotion_feed failed: status=%s body=%s",
                resp.status_code,
                resp.text[:2000],
            )
    except Exception as exc:
        logger.error("Failed to insert friend_emotion_feed rows: %s", exc)


async def _notify_friends_about_emotion(
    *,
    owner_user_id: str,
    emotion_details: List[Dict[str, Any]],
    created_at: str,
) -> None:
    """感情ログ登録後に、フレンド向けの通知レコードを friend_emotion_feed に作成する。"""
    if not owner_user_id:
        return

    viewer_user_ids = await _fetch_friend_viewer_ids(owner_user_id)
    if not viewer_user_ids:
        # フレンドがいない場合は何もしない
        return

    owner_name = await _fetch_profile_display_name(owner_user_id)
    await _insert_friend_emotion_feed_rows(
        viewer_user_ids=viewer_user_ids,
        owner_user_id=owner_user_id,
        owner_name=owner_name,
        items=emotion_details,
        created_at=created_at,
    )

    # Push notification (FCM). 失敗しても感情ログ本体は成功させたいので best-effort。
    try:
        await _push_notify_friends_about_emotion(
            viewer_user_ids=viewer_user_ids,
            owner_user_id=owner_user_id,
            owner_name=owner_name,
            emotion_details=emotion_details,
            created_at=created_at,
        )
    except Exception as exc:
        logger.error("Failed to send FCM push notification: %s", exc)



# ---------- Post-submit background processing ----------
# 目的:
# - ユーザー体感の入力処理を短縮するため、感情保存(insert)後の重い処理をバックグラウンドで実行する。
# - 具体的には、フレンド通知 / ASTOR ingest / MyProfile latest auto-refresh をレスポンス後に回す。
#
# NOTE:
# - Render 環境での安定性を優先し、別スレッドで asyncio.run() を使って完結させる。
# - 失敗しても emotion/submit 自体は成功として扱う（入力保存を優先）。

async def _post_submit_background_async(
    *,
    user_id: str,
    emotion_details: List[Dict[str, Any]],
    created_at: str,
    avg_strength: Optional[float],
    memo: Optional[str],
    is_secret: bool,
    notify_friends: bool,
) -> None:
    # 1) フレンド通知（Friend タブ用タイムライン + Push）
    if notify_friends:
        try:
            await _notify_friends_about_emotion(
                owner_user_id=user_id,
                emotion_details=emotion_details,
                created_at=created_at,
            )
        except Exception as exc:
            logger.error("Failed to notify friends about emotion (bg): %s", exc)

    # 2) ASTOR への感情インジェスト（失敗しても致命的ではない）
    try:
        astor_payload = AstorEmotionPayload(
            user_id=user_id,
            created_at=created_at,
            emotions=emotion_details,
            emotion_strength_avg=avg_strength if avg_strength is not None else 0.0,
            memo=memo,
            is_secret=bool(is_secret),
        )
        astor_req = AstorRequest(
            mode=AstorMode.EMOTION_INGEST,
            emotion=astor_payload,
        )
        try:
            astor_engine.handle(astor_req)
        except Exception as exc:
            logger.error("ASTOR EmotionIngest failed (bg): %s", exc)

        # 3) MyProfile 最新レポート（プレビュー）を自動更新（失敗しても致命的ではない）
        try:
            await _auto_refresh_myprofile_latest_report(user_id)
        except Exception as exc:
            logger.error("MyProfile latest auto-refresh failed (bg): %s", exc)
    except Exception as exc:
        logger.error("ASTOR background pipeline failed (bg): %s", exc)


def _post_submit_background_thread_entry(
    *,
    user_id: str,
    emotion_details: List[Dict[str, Any]],
    created_at: str,
    avg_strength: Optional[float],
    memo: Optional[str],
    is_secret: bool,
    notify_friends: bool,
) -> None:
    try:
        asyncio.run(
            _post_submit_background_async(
                user_id=user_id,
                emotion_details=emotion_details,
                created_at=created_at,
                avg_strength=avg_strength,
                memo=memo,
                is_secret=is_secret,
                notify_friends=notify_friends,
            )
        )
    except Exception as exc:
        logger.error("post-submit background thread failed: %s", exc)


def _start_post_submit_background_tasks(
    *,
    user_id: str,
    emotion_details: List[Dict[str, Any]],
    created_at: str,
    avg_strength: Optional[float],
    memo: Optional[str],
    is_secret: bool,
    notify_friends: bool,
) -> None:
    try:
        t = threading.Thread(
            target=_post_submit_background_thread_entry,
            kwargs={
                "user_id": user_id,
                "emotion_details": emotion_details,
                "created_at": created_at,
                "avg_strength": avg_strength,
                "memo": memo,
                "is_secret": is_secret,
                "notify_friends": notify_friends,
            },
            daemon=True,
        )
        t.start()
    except Exception as exc:
        logger.error("Failed to start post-submit background tasks: %s", exc)


# ---------- Route registration ----------


def register_emotion_submit_routes(app: FastAPI) -> None:
    """
    与えられた FastAPI インスタンスに /emotion/submit エンドポイントを登録する。
    - app.py 側から `register_emotion_submit_routes(app)` を呼び出して利用する想定。
    """

    @app.post("/emotion/submit", response_model=EmotionSubmitResponse)
    async def emotion_submit(
        payload: EmotionSubmitRequest,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> EmotionSubmitResponse:
        # 1) ユーザーIDを確定
        access_token = _extract_bearer_token(authorization)

        if access_token:
            user_id = await _resolve_user_id_from_token(access_token)
        else:
            # Authorization が無い場合は、原則 401。
            if ALLOW_LEGACY_USER_ID and payload.user_id:
                logger.warning(
                    "Authorization header is missing; falling back to payload.user_id (legacy mode)."
                )
                user_id = payload.user_id  # type: ignore[assignment]
            else:
                raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        # 2) emotions を正規化
        emotions_tags, emotion_details, avg_strength = _normalize_emotions(payload.emotions)

        if not emotions_tags:
            raise HTTPException(status_code=400, detail="At least one emotion is required")

        # 3) created_at を決定
        if payload.created_at:
            created_at = payload.created_at
        else:
            created_at = datetime.now(timezone.utc).isoformat()

        # 4) Supabase の emotions に INSERT
        inserted = await _insert_emotion_row(
            user_id=user_id,
            emotions=emotions_tags,
            emotion_details=emotion_details,
            emotion_strength_avg=avg_strength,
            memo=payload.memo,
            created_at=created_at,
            is_secret=bool(payload.is_secret),
        )

        # 5) 残りの重い処理（通知/分析/レポート更新）はバックグラウンドで実行する
        # - notify_friends=false（または send_friend_notification=false）の場合は通知しない。
        notify_friends = True if payload.notify_friends is None else bool(payload.notify_friends)
        _start_post_submit_background_tasks(
            user_id=user_id,
            emotion_details=emotion_details,
            created_at=created_at,
            avg_strength=avg_strength,
            memo=payload.memo,
            is_secret=bool(payload.is_secret),
            notify_friends=notify_friends,
        )

        return EmotionSubmitResponse(
            status="ok",
            id=inserted.get("id"),
            created_at=inserted.get("created_at", created_at),
        )

