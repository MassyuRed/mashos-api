# -*- coding: utf-8 -*-
"""middleware_active_user_touch.py (Phase 8++++++)

目的
- "touchしたいAPIがトークン解決を通らないケース" を吸収するため、FastAPI middleware で
  *成功したリクエスト* を best-effort に active_users へ touch する。

既存の拡張（前パッチ）
1) JWT 未検証デコードを避ける
   - Supabase Auth (GET /auth/v1/user) で access token を検証して user_id を取得
   - 短TTLのプロセス内キャッシュで通信回数を抑える
2) touch 対象の制御を柔軟化
   - include / exclude を正規表現で指定可能
3) create_task のスケジュールを間引く
   - 同一キーに対して in-flight 抑止 + 最短N秒間隔

今回の拡張（キー設計のチューニング）
- "同一トークン×全パスで1本" など、path を粗くして create_task をさらに減らせるようにする
- ただし、"重要パス" は間引きを弱めたい（=より頻繁に touch したい）ので、
  - キーの粒度（path mode）
  - 最短間隔（min interval）
  を重要パスだけ上書きできるようにする

方針
- Authorization: Bearer <access_token> がある場合のみ対象。
- デフォルトでは "レスポンスが成功(<400)" の時だけ touch。
- Middleware 自体は *ルーティングの認可・権限制御を置き換えない*。
  ここは「アクティブ判定」のための best-effort 更新のみ。

ENV
- ACTIVE_USERS_MIDDLEWARE_ENABLED (default: true)
- ACTIVE_USERS_MIDDLEWARE_TOUCH_ON_SUCCESS_ONLY (default: true)

除外（簡易）
- ACTIVE_USERS_MIDDLEWARE_EXCLUDED_PATH_PREFIXES
  default: /healthz,/docs,/redoc,/openapi.json,/favicon.ico,/cron
- ACTIVE_USERS_MIDDLEWARE_EXCLUDED_METHODS (default: OPTIONS)

除外/包含（正規表現）
- ACTIVE_USERS_MIDDLEWARE_INCLUDE_PATH_REGEXES
  例: ^/myweb/ , ^/myprofile/ , ^/deep_insight/
  未指定なら「全て対象（prefix除外は別途）」
- ACTIVE_USERS_MIDDLEWARE_EXCLUDE_PATH_REGEXES
  例: ^/mymodel/templates$ , ^/mymodel/infer$
  指定されていれば exclude が優先

Supabase検証（短TTLキャッシュ）
- ACTIVE_USERS_MIDDLEWARE_VERIFY_WITH_SUPABASE (default: true)
- ACTIVE_USERS_MIDDLEWARE_AUTH_CACHE_TTL_SECONDS (default: 60)
- ACTIVE_USERS_MIDDLEWARE_AUTH_NEGATIVE_TTL_SECONDS (default: 10)
- ACTIVE_USERS_MIDDLEWARE_AUTH_CACHE_MAX_SIZE (default: 2048)
- ACTIVE_USERS_MIDDLEWARE_AUTH_TIMEOUT_SECONDS (default: 3.0)

スケジュール間引き（create_task）
- ACTIVE_USERS_MIDDLEWARE_SCHEDULE_MIN_INTERVAL_SECONDS (default: 5)
  同一キーで create_task する最短間隔（秒）
  0 にすると「in-flight 抑止のみ」になります
- ACTIVE_USERS_MIDDLEWARE_SCHEDULE_KEY_INCLUDE_METHOD (default: true)
  true の場合、キーに HTTP method も含める（GET/POST を別扱い）
- ACTIVE_USERS_MIDDLEWARE_SCHEDULE_CACHE_MAX_SIZE (default: 4096)
  プロセス内LRUの最大キー数（メモリ上限）

キー粒度（path を粗くする）
- ACTIVE_USERS_MIDDLEWARE_SCHEDULE_KEY_PATH_MODE (default: full)
  - full   : /myweb/reports/ensure のようにフルパスをキーに含める（従来）
  - prefix : 先頭Nセグメントだけをキーに含める
  - none   : path をキーに含めない（=同一トークン×全パスで1本）
- ACTIVE_USERS_MIDDLEWARE_SCHEDULE_PATH_PREFIX_SEGMENTS (default: 1)
  prefix の場合、何セグメント分採るか

重要パス（間引きを弱める）
- ACTIVE_USERS_MIDDLEWARE_SCHEDULE_IMPORTANT_PATH_REGEXES (default: empty)
  例: ^/emotion/submit$,^/myprofile/latest$
- ACTIVE_USERS_MIDDLEWARE_SCHEDULE_IMPORTANT_KEY_PATH_MODE (default: full)
  重要パスだけキー粒度を変えたい場合（例: デフォ none だけど重要は full）
- ACTIVE_USERS_MIDDLEWARE_SCHEDULE_IMPORTANT_PATH_PREFIX_SEGMENTS (default: same as PATH_PREFIX_SEGMENTS)
  important_key_path_mode=prefix の時に使用
- ACTIVE_USERS_MIDDLEWARE_SCHEDULE_IMPORTANT_MIN_INTERVAL_SECONDS (default: -1)
  -1 の場合はデフォルト（SCHEDULE_MIN_INTERVAL_SECONDS）を使う

最短間隔の個別上書き（正規表現）
- ACTIVE_USERS_MIDDLEWARE_SCHEDULE_MIN_INTERVAL_OVERRIDES
  例: ^/emotion/submit$=0,^/myprofile/latest$=1
  ※ 先にマッチしたものが優先

フォールバック（任意 / 非推奨）
- ACTIVE_USERS_MIDDLEWARE_FALLBACK_TO_UNVERIFIED_SUB (default: false)
  Supabase 検証が使えない環境で、従来どおり sub を未検証デコードして touch したい場合のみ。

注意
- この間引きは「プロセス内」です（複数インスタンス/複数ワーカー間では共有されません）。
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import logging
import os
import re
import threading
import time
from collections import OrderedDict
from typing import Optional

from fastapi import FastAPI
from starlette.requests import Request

from active_users_store import touch_active_user
from supabase_auth_token_cache import resolve_user_id_verified_cached

logger = logging.getLogger("middleware_active_user_touch")


_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)


def _env_truthy(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in ("1", "true", "yes", "y", "on")


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(str(raw).strip())
    except Exception:
        return default


def _split_csv(raw: str) -> list[str]:
    return [s.strip() for s in (raw or "").split(",") if s.strip()]


def _extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer" and parts[1]:
        return parts[1]
    return None


def _compile_regexes(raw: Optional[str]) -> list[re.Pattern]:
    patterns: list[re.Pattern] = []
    for s in _split_csv(raw or ""):
        try:
            patterns.append(re.compile(s))
        except Exception:
            logger.warning("Invalid regex ignored: %s", s)
    return patterns


def _parse_regex_int_overrides(raw: Optional[str]) -> list[tuple[re.Pattern, float]]:
    """Parse REGEX=SECONDS,REGEX=SECONDS ..."""
    out: list[tuple[re.Pattern, float]] = []
    for item in _split_csv(raw or ""):
        if "=" not in item:
            logger.warning(
                "Invalid override ignored (expected REGEX=SECONDS): %s", item
            )
            continue
        pat_s, sec_s = item.split("=", 1)
        pat_s = pat_s.strip()
        sec_s = sec_s.strip()
        if not pat_s:
            continue
        try:
            pat = re.compile(pat_s)
        except Exception:
            logger.warning("Invalid override regex ignored: %s", pat_s)
            continue
        try:
            sec = float(sec_s)
        except Exception:
            logger.warning("Invalid override seconds ignored: %s", item)
            continue
        if sec < 0:
            sec = 0.0
        out.append((pat, sec))
    return out


def _b64url_decode(seg: str) -> bytes:
    s = seg.strip()
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def _extract_user_id_from_jwt_unverified(token: str) -> Optional[str]:
    """Unverified fallback (NOT recommended).

    Only used when ACTIVE_USERS_MIDDLEWARE_FALLBACK_TO_UNVERIFIED_SUB=true.
    """

    tok = str(token or "").strip()
    if not tok:
        return None

    parts = tok.split(".")
    if len(parts) < 2:
        return None

    try:
        payload_bytes = _b64url_decode(parts[1])
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception:
        return None

    # best-effort exp check
    try:
        exp = payload.get("exp")
        if isinstance(exp, (int, float)) and float(exp) < time.time() - 5:
            return None
    except Exception:
        pass

    uid = str(payload.get("sub") or "").strip()
    if not uid:
        return None
    if not _UUID_RE.match(uid):
        return None
    return uid


# -------------------------
# Scheduling debounce / rate limit (process local)
# -------------------------
_DEFAULT_SCHEDULE_MIN_INTERVAL = max(
    0, _env_int("ACTIVE_USERS_MIDDLEWARE_SCHEDULE_MIN_INTERVAL_SECONDS", 5)
)
_SCHEDULE_KEY_INCLUDE_METHOD = _env_truthy(
    "ACTIVE_USERS_MIDDLEWARE_SCHEDULE_KEY_INCLUDE_METHOD", True
)

# Key design tuning
_SCHEDULE_KEY_PATH_MODE = (
    os.getenv("ACTIVE_USERS_MIDDLEWARE_SCHEDULE_KEY_PATH_MODE", "full") or "full"
).strip().lower()
_SCHEDULE_PATH_PREFIX_SEGMENTS = max(
    1, _env_int("ACTIVE_USERS_MIDDLEWARE_SCHEDULE_PATH_PREFIX_SEGMENTS", 1)
)

_IMPORTANT_PATH_REGEXES = _compile_regexes(
    os.getenv("ACTIVE_USERS_MIDDLEWARE_SCHEDULE_IMPORTANT_PATH_REGEXES")
)
_IMPORTANT_KEY_PATH_MODE = (
    os.getenv("ACTIVE_USERS_MIDDLEWARE_SCHEDULE_IMPORTANT_KEY_PATH_MODE", "full")
    or "full"
).strip().lower()
_IMPORTANT_PATH_PREFIX_SEGMENTS = max(
    1,
    _env_int(
        "ACTIVE_USERS_MIDDLEWARE_SCHEDULE_IMPORTANT_PATH_PREFIX_SEGMENTS",
        _SCHEDULE_PATH_PREFIX_SEGMENTS,
    ),
)

_IMPORTANT_MIN_INTERVAL = _env_int(
    "ACTIVE_USERS_MIDDLEWARE_SCHEDULE_IMPORTANT_MIN_INTERVAL_SECONDS", -1
)

_MIN_INTERVAL_OVERRIDES = _parse_regex_int_overrides(
    os.getenv("ACTIVE_USERS_MIDDLEWARE_SCHEDULE_MIN_INTERVAL_OVERRIDES")
)


def _normalize_path_mode(mode: str) -> str:
    m = (mode or "").strip().lower()
    if m in ("full", "path"):
        return "full"
    if m in ("prefix", "seg", "segment", "segments"):
        return "prefix"
    if m in ("none", "token", "token_only", "global", "all"):
        return "none"
    logger.warning("Unknown schedule key path mode '%s' -> fallback to 'full'", mode)
    return "full"


def _path_key_for_mode(path: str, mode: str, prefix_segments: int) -> str:
    m = _normalize_path_mode(mode)

    if m == "none":
        return "*"  # constant; indicates "all paths".

    if m == "prefix":
        # Take first N segments.
        # '/myweb/reports/ensure' -> '/myweb' (N=1), '/myweb/reports' (N=2)
        parts = [p for p in (path or "").split("/") if p]
        if not parts:
            return "/"
        return "/" + "/".join(parts[: max(1, int(prefix_segments))])

    # full
    return path or "/"


def _is_important_path(path: str) -> bool:
    if not _IMPORTANT_PATH_REGEXES:
        return False
    try:
        return any(r.search(path) for r in _IMPORTANT_PATH_REGEXES)
    except Exception:
        return False


def _effective_min_interval_seconds(path: str, important: bool) -> float:
    # Regex overrides are highest priority.
    for r, sec in _MIN_INTERVAL_OVERRIDES:
        try:
            if r.search(path):
                return float(sec)
        except Exception:
            continue

    if important and _IMPORTANT_MIN_INTERVAL >= 0:
        return float(_IMPORTANT_MIN_INTERVAL)

    return float(_DEFAULT_SCHEDULE_MIN_INTERVAL)


# key -> last_scheduled_monotonic
_SCHED_LOCK = threading.Lock()
_SCHED_LAST: "OrderedDict[str, float]" = OrderedDict()
_SCHED_INFLIGHT: set[str] = set()
_SCHED_MAX_SIZE = max(
    256, _env_int("ACTIVE_USERS_MIDDLEWARE_SCHEDULE_CACHE_MAX_SIZE", 4096)
)


def _digest_token(token: str) -> str:
    # Do not keep token in memory as a key; store only sha256 digest.
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _build_schedule_key(token: str, method: str, path_key: str) -> str:
    d = _digest_token(token)
    if _SCHEDULE_KEY_INCLUDE_METHOD:
        return f"{d}:{method}:{path_key}"
    return f"{d}:{path_key}"


def _try_acquire_schedule(key: str, min_interval_seconds: float) -> bool:
    """Return True if we should schedule a background task for this key."""

    # Only suppress if in-flight; otherwise always schedule.
    # (Still keep 'last' updated so non-important keys can be rate-limited later.)
    if min_interval_seconds <= 0:
        with _SCHED_LOCK:
            if key in _SCHED_INFLIGHT:
                return False
            _SCHED_INFLIGHT.add(key)
            _SCHED_LAST[key] = time.monotonic()
            _SCHED_LAST.move_to_end(key)
            while len(_SCHED_LAST) > _SCHED_MAX_SIZE:
                old_key, _ = _SCHED_LAST.popitem(last=False)
                _SCHED_INFLIGHT.discard(old_key)
        return True

    now = time.monotonic()
    with _SCHED_LOCK:
        if key in _SCHED_INFLIGHT:
            return False

        last = _SCHED_LAST.get(key)
        if last is not None and (now - last) < float(min_interval_seconds):
            # LRU refresh
            try:
                _SCHED_LAST.move_to_end(key)
            except Exception:
                pass
            return False

        _SCHED_INFLIGHT.add(key)
        _SCHED_LAST[key] = now
        try:
            _SCHED_LAST.move_to_end(key)
        except Exception:
            pass

        # Evict LRU to keep memory bounded
        while len(_SCHED_LAST) > _SCHED_MAX_SIZE:
            try:
                old_key, _ = _SCHED_LAST.popitem(last=False)
                _SCHED_INFLIGHT.discard(old_key)
            except Exception:
                break

        return True


def _release_schedule(key: str) -> None:
    with _SCHED_LOCK:
        _SCHED_INFLIGHT.discard(key)


def install_active_user_touch_middleware(app: FastAPI) -> None:
    if not _env_truthy("ACTIVE_USERS_MIDDLEWARE_ENABLED", True):
        return

    touch_on_success_only = _env_truthy(
        "ACTIVE_USERS_MIDDLEWARE_TOUCH_ON_SUCCESS_ONLY", True
    )

    excluded_prefixes = _split_csv(
        os.getenv(
            "ACTIVE_USERS_MIDDLEWARE_EXCLUDED_PATH_PREFIXES",
            "/healthz,/docs,/redoc,/openapi.json,/favicon.ico,/cron",
        )
    )

    excluded_methods = set(
        m.strip().upper()
        for m in _split_csv(os.getenv("ACTIVE_USERS_MIDDLEWARE_EXCLUDED_METHODS", "OPTIONS"))
    )

    include_path_regexes = _compile_regexes(
        os.getenv("ACTIVE_USERS_MIDDLEWARE_INCLUDE_PATH_REGEXES")
    )
    exclude_path_regexes = _compile_regexes(
        os.getenv("ACTIVE_USERS_MIDDLEWARE_EXCLUDE_PATH_REGEXES")
    )

    fallback_unverified = _env_truthy(
        "ACTIVE_USERS_MIDDLEWARE_FALLBACK_TO_UNVERIFIED_SUB", False
    )

    def _should_consider(path: str, method: str) -> bool:
        if method in excluded_methods:
            return False
        if any(path.startswith(p) for p in excluded_prefixes):
            return False
        if exclude_path_regexes and any(r.search(path) for r in exclude_path_regexes):
            return False
        if include_path_regexes and not any(r.search(path) for r in include_path_regexes):
            return False
        return True

    async def _verify_and_touch(token: str, activity: str) -> None:
        # Verified + cached resolve
        uid = await resolve_user_id_verified_cached(token)

        # Optional fallback (not recommended)
        if not uid and fallback_unverified:
            uid = _extract_user_id_from_jwt_unverified(token)

        if not uid:
            return

        try:
            await touch_active_user(uid, activity=activity)
        except Exception:
            # touch is best-effort
            return

    async def _verify_touch_with_release(token: str, activity: str, sched_key: str) -> None:
        try:
            await _verify_and_touch(token, activity)
        finally:
            _release_schedule(sched_key)

    @app.middleware("http")
    async def _active_user_touch_middleware(request: Request, call_next):
        path = request.url.path or ""
        method = (request.method or "").upper()

        if not _should_consider(path, method):
            return await call_next(request)

        token = _extract_bearer_token(request.headers.get("authorization"))

        response = await call_next(request)

        if not token:
            return response

        if touch_on_success_only and int(response.status_code) >= 400:
            return response

        activity = f"{method} {path}"[:120]

        important = _is_important_path(path)

        # Key design tuning:
        # - default path mode is configurable (full/prefix/none)
        # - important paths can override the path mode
        if important:
            path_key = _path_key_for_mode(
                path, _IMPORTANT_KEY_PATH_MODE, _IMPORTANT_PATH_PREFIX_SEGMENTS
            )
        else:
            path_key = _path_key_for_mode(path, _SCHEDULE_KEY_PATH_MODE, _SCHEDULE_PATH_PREFIX_SEGMENTS)

        min_interval = _effective_min_interval_seconds(path, important)

        # Debounce scheduling to avoid excessive create_task
        sched_key = _build_schedule_key(token, method, path_key)
        if not _try_acquire_schedule(sched_key, min_interval):
            return response

        # Run in background so we don't add latency to the request.
        try:
            asyncio.create_task(_verify_touch_with_release(token, activity, sched_key))
        except Exception:
            # If create_task fails, run inline (still best-effort) and release the key.
            try:
                await _verify_touch_with_release(token, activity, sched_key)
            except Exception:
                pass

        return response
