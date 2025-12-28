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
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

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
    """Firebase Admin SDK を初期化する（FCM HTTP v1 用）。"""
    global _FCM_APP_INITIALIZED

    if _FCM_APP_INITIALIZED:
        return True

    with _FCM_APP_INIT_LOCK:
        if _FCM_APP_INITIALIZED:
            return True

        try:
            import firebase_admin
            from firebase_admin import credentials
        except Exception as exc:
            logger.error("firebase-admin is not available: %s", exc)
            return False

        # すでに初期化済みならOK
        try:
            firebase_admin.get_app()
            _FCM_APP_INITIALIZED = True
            return True
        except Exception:
            pass

        cred_path = _ensure_fcm_service_account_file()
        if not cred_path:
            return False

        try:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            _FCM_APP_INITIALIZED = True
            logger.info("Firebase Admin SDK initialized for FCM push (v1).")
            return True
        except Exception as exc:
            logger.error("Failed to initialize Firebase Admin SDK: %s", exc)
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
        parts.append(f"{t}{f'（{label}）' if label else ''}")

    if not parts:
        return "フレンドが感情を入力しました"

    # 例: 喜び（強） / 不安（弱）
    body = " / ".join(parts)
    return body[:180]


async def _fetch_push_tokens_for_users(user_ids: List[str]) -> Dict[str, str]:
    """profiles から push_token を取得する（service_roleでRLSをバイパス）。"""
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
    params = {
        "select": "id,push_token",
        "id": f"in.({quoted})",
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
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


async def _send_fcm_push_v1(
    *,
    tokens: List[str],
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
) -> None:
    """FCM HTTP v1 (Firebase Admin SDK) で push を送る（best-effort）。"""
    if not (FCM_PUSH_ENABLED and _has_fcm_v1_credentials()):
        return
    if not _ensure_firebase_admin_initialized():
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
            if k is None:
                continue
            if v is None:
                continue
            data_str[str(k)] = str(v)

    # Multicast は最大 500 tokens（安全側で 450）
    batches = _chunk_list(uniq, 450)

    async def _send_one_batch(batch_tokens: List[str]):
        def _send_sync():
            from firebase_admin import messaging

            msg = messaging.MulticastMessage(
                tokens=batch_tokens,
                notification=messaging.Notification(title=title, body=body),
                data=data_str or None,
                android=messaging.AndroidConfig(priority="high"),
            )

            send_each = getattr(messaging, "send_each_for_multicast", None)
            if callable(send_each):
                return send_each(msg)

            send_multi = getattr(messaging, "send_multicast", None)
            if callable(send_multi):
                return send_multi(msg)

            raise RuntimeError("firebase_admin.messaging does not support multicast send on this version")

        return await asyncio.to_thread(_send_sync)

    for batch in batches:
        try:
            resp = await _send_one_batch(batch)
            success = getattr(resp, "success_count", None)
            failure = getattr(resp, "failure_count", None)
            logger.info("FCM v1 push sent: success=%s failure=%s", success, failure)

            if failure:
                responses = getattr(resp, "responses", None)
                if isinstance(responses, list):
                    errs = []
                    for r in responses:
                        try:
                            ok = getattr(r, "success", True)
                            if ok:
                                continue
                            exc = getattr(r, "exception", None)
                            if exc:
                                errs.append(str(exc))
                        except Exception:
                            continue
                    if errs:
                        logger.warning("FCM v1 push failures (sample): %s", errs[:5])
        except Exception as exc:
            logger.error("FCM v1 push send failed: %s", exc)


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
                "notification": {"title": title, "body": body},
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

    title = f"{owner_name}の感情が更新されました"
    body = _format_emotion_push_body(emotion_details)

    data: Dict[str, Any] = {
        "type": "friend_emotion",
        "owner_user_id": owner_user_id,
        "created_at": created_at,
    }

    await _send_fcm_push(tokens=tokens, title=title, body=body, data=data)
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

        # 5) フレンドへの通知（Frend タブ用タイムライン）
        # 失敗しても感情ログ本体は成功させたいので、例外は握りつぶす。
        try:
            await _notify_friends_about_emotion(
                owner_user_id=user_id,
                emotion_details=emotion_details,
                created_at=created_at,
            )
        except Exception as exc:
            logger.error("Failed to notify friends about emotion: %s", exc)

        # 6) ASTOR への感情インジェスト（失敗しても致命的ではない）
        try:
            astor_payload = AstorEmotionPayload(
                user_id=user_id,
                created_at=created_at,
                emotions=emotion_details,
                emotion_strength_avg=avg_strength if avg_strength is not None else 0.0,
                memo=payload.memo,
                is_secret=bool(payload.is_secret),
            )
            astor_req = AstorRequest(
                mode=AstorMode.EMOTION_INGEST,
                emotion=astor_payload,
            )
            astor_engine.handle(astor_req)
        except Exception as exc:
            logger.error("ASTOR EmotionIngest failed: %s", exc)

        return EmotionSubmitResponse(
            status="ok",
            id=inserted.get("id"),
            created_at=inserted.get("created_at", created_at),
        )

