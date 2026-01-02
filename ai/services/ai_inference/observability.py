# -*- coding: utf-8 -*-
"""observability.py

Phase11: 監視/ログ/通知の可観測性
--------------------------------

目的
- 障害発生時に「どこで止まっているか」を素早く特定できるようにする。
- Cron 実行結果（generated / exists / errors）を確実にログへ残す。
- Supabase 502 / timeout など外部依存の失敗を、ログと（任意で）Slack通知で見える化する。

方針
- logging に JSON 文字列を流し、Renderのログや外部ログ基盤で絞り込めるようにする。
- Slack通知は best-effort（失敗しても本処理は落とさない）
- 機微情報（Bearer token 等）はログに出さない

主な環境変数
- OBS_LOG_JSON=true/false（default true）

Slack（Incoming Webhook）
- SLACK_WEBHOOK_URL=<incoming webhook url>
- SLACK_NOTIFY_ENABLED=true/false（default: webhookがあればtrue扱い）
- SLACK_TIMEOUT_SECONDS=3.0
- SLACK_RATE_LIMIT_SECONDS=60
- SLACK_NOTIFY_ON_CRON_ERRORS=true/false（default true）
- SLACK_NOTIFY_ON_CRON_FAILURE=true/false（default true）
- SLACK_INCLUDE_ERROR_SAMPLES=true/false（default false）
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx


# ----------------------------
# JSON logging
# ----------------------------

OBS_LOG_JSON = (os.getenv("OBS_LOG_JSON", "true").strip().lower() != "false")
# Render log alert helpers
# - Render のログアラートは JSON のフィールド抽出が難しいことがあるため、
#   安定したプレーン文字列（ALERT::KEY ...）も出せるようにする。
OBS_RENDER_ALERT_MARKERS_ENABLED = (os.getenv("OBS_RENDER_ALERT_MARKERS_ENABLED", "true").strip().lower() != "false")
OBS_RENDER_ALERT_PREFIX = (os.getenv("OBS_RENDER_ALERT_PREFIX", "ALERT::") or "ALERT::").strip() or "ALERT::"
try:
    OBS_RENDER_ALERT_KV_MAX_LEN = int(os.getenv("OBS_RENDER_ALERT_KV_MAX_LEN", "200") or "200")
except Exception:
    OBS_RENDER_ALERT_KV_MAX_LEN = 200



def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _safe_default(o: Any) -> str:
    try:
        return str(o)
    except Exception:
        return repr(o)


def _safe_json_dumps(obj: Dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), default=_safe_default)


def log_event(logger: logging.Logger, event: str, *, level: str = "info", **fields: Any) -> None:
    """Write a structured event log.

    - level: info|warning|error|debug
    - event: stable identifier (e.g., cron_batch_complete)
    """
    payload: Dict[str, Any] = {
        "ts": _iso_now(),
        "event": event,
        **fields,
    }

    msg = _safe_json_dumps(payload) if OBS_LOG_JSON else f"{event} {payload}"

    try:
        fn = getattr(logger, level, logger.info)
        fn(msg)
    except Exception:
        # Never crash caller due to logging failures
        try:
            logger.info(msg)
        except Exception:
            pass



def _compact_kv(fields: Dict[str, Any]) -> str:
    """Compact key/value rendering for alert marker lines.

    - Keeps it single-line for log alerts.
    - Truncates long values.
    """
    parts = []
    for k, v in (fields or {}).items():
        if v is None:
            continue
        try:
            s = str(v)
        except Exception:
            s = repr(v)
        s = s.replace("\n", " ").replace("\r", " ").strip()
        if OBS_RENDER_ALERT_KV_MAX_LEN > 0 and len(s) > OBS_RENDER_ALERT_KV_MAX_LEN:
            s = s[: max(0, OBS_RENDER_ALERT_KV_MAX_LEN - 3)] + "..."
        parts.append(f"{k}={s}")
    return " ".join(parts)


def log_alert(
    logger: logging.Logger,
    alert_key: str,
    *,
    level: str = "warning",
    message: Optional[str] = None,
    event: str = "alert",
    **fields: Any,
) -> None:
    """Emit an alert-friendly log.

    - JSONログ: event="alert", alert_key=...
    - Render等での簡易アラート: 'ALERT::KEY ...' のプレーン文字列も出せる（任意）
    """
    safe_fields: Dict[str, Any] = dict(fields or {})
    safe_fields["alert_key"] = alert_key
    if message:
        safe_fields["message"] = message

    # Structured log (JSON)
    log_event(logger, event, level=level, **safe_fields)

    # Plain marker line (easier grep/alert on Render)
    if OBS_RENDER_ALERT_MARKERS_ENABLED:
        try:
            kv = _compact_kv({k: v for k, v in safe_fields.items() if k not in ("message",)})
            line = f"{OBS_RENDER_ALERT_PREFIX}{alert_key}"
            if kv:
                line = f"{line} {kv}"
            getattr(logger, level, logger.warning)(line)
        except Exception:
            pass

# ----------------------------
# Slack notifier (incoming webhook)
# ----------------------------

SLACK_WEBHOOK_URL = (os.getenv("SLACK_WEBHOOK_URL") or "").strip()
SLACK_NOTIFY_ENABLED = (
    (os.getenv("SLACK_NOTIFY_ENABLED") or "").strip().lower() in ("1", "true", "yes")
) or bool(SLACK_WEBHOOK_URL)

try:
    SLACK_TIMEOUT_SECONDS = float(os.getenv("SLACK_TIMEOUT_SECONDS", "3.0") or "3.0")
except Exception:
    SLACK_TIMEOUT_SECONDS = 3.0

try:
    SLACK_RATE_LIMIT_SECONDS = float(os.getenv("SLACK_RATE_LIMIT_SECONDS", "60") or "60")
except Exception:
    SLACK_RATE_LIMIT_SECONDS = 60.0

SLACK_NOTIFY_ON_CRON_ERRORS = (os.getenv("SLACK_NOTIFY_ON_CRON_ERRORS", "true").strip().lower() != "false")
SLACK_NOTIFY_ON_CRON_FAILURE = (os.getenv("SLACK_NOTIFY_ON_CRON_FAILURE", "true").strip().lower() != "false")
SLACK_INCLUDE_ERROR_SAMPLES = (
    os.getenv("SLACK_INCLUDE_ERROR_SAMPLES", "false").strip().lower() in ("1", "true", "yes")
)


@dataclass
class SlackSendResult:
    sent: bool
    skipped: bool
    reason: str = ""


_last_sent_at: Dict[str, float] = {}
_last_sent_lock = asyncio.Lock()


def _hash_key(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()[:16]


async def _rate_limit_allow(key: str) -> bool:
    """Simple in-process rate limit by key."""
    if SLACK_RATE_LIMIT_SECONDS <= 0:
        return True
    now = time.monotonic()
    async with _last_sent_lock:
        last = _last_sent_at.get(key)
        if last is not None and (now - last) < SLACK_RATE_LIMIT_SECONDS:
            return False
        _last_sent_at[key] = now
        return True


def _truncate(s: str, max_len: int = 1200) -> str:
    s = str(s or "")
    if len(s) <= max_len:
        return s
    return s[: max_len - 3] + "..."


async def send_slack_webhook(
    *,
    text: str,
    title: Optional[str] = None,
    key: Optional[str] = None,
    timeout_seconds: Optional[float] = None,
) -> SlackSendResult:
    """Send a slack webhook message (best-effort)."""
    if not SLACK_NOTIFY_ENABLED or not SLACK_WEBHOOK_URL:
        return SlackSendResult(sent=False, skipped=True, reason="disabled")

    k = _hash_key(key or title or text[:80] or "slack")
    allowed = await _rate_limit_allow(k)
    if not allowed:
        return SlackSendResult(sent=False, skipped=True, reason="rate_limited")

    body_text = text
    if title:
        body_text = f"*{title}*\n{body_text}"

    payload = {"text": _truncate(body_text, 3500)}
    t = float(timeout_seconds or SLACK_TIMEOUT_SECONDS)

    try:
        async with httpx.AsyncClient(timeout=t) as client:
            resp = await client.post(SLACK_WEBHOOK_URL, json=payload)
        if 200 <= resp.status_code < 300:
            return SlackSendResult(sent=True, skipped=False, reason="ok")
        return SlackSendResult(sent=False, skipped=False, reason=f"http_{resp.status_code}")
    except Exception as exc:
        return SlackSendResult(sent=False, skipped=False, reason=f"exception:{type(exc).__name__}")


# ----------------------------
# Run context helpers
# ----------------------------

def new_run_id(prefix: str = "run") -> str:
    """Short run id for correlation."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def monotonic_ms() -> float:
    return time.monotonic() * 1000.0


def elapsed_ms(start_ms: float) -> int:
    try:
        return int(max(0.0, monotonic_ms() - float(start_ms)))
    except Exception:
        return 0
