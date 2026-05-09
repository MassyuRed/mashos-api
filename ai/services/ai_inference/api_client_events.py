from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional

from fastapi import FastAPI, Header, Request
from pydantic import BaseModel, Field

from api_emotion_submit import _extract_bearer_token, _resolve_user_id_from_token
from client_compat import extract_client_meta
from observability import log_alert, log_event

logger = logging.getLogger("client_events")

CLIENT_EVENT_SCHEMA_VERSION = "ops.client_event.v1"
MAX_TEXT_LEN = 800
MAX_META_KEYS = 32
REDACTED_KEYS = {"authorization", "token", "access_token", "refresh_token", "password", "secret", "api_key", "apikey"}

_EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
_UUID_RE = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b", re.IGNORECASE)
_TOKENISH_RE = re.compile(r"\b(?:Bearer\s+)?[A-Za-z0-9_=-]{24,}(?:\.[A-Za-z0-9_=-]{8,}){0,2}\b")


class ClientEventRequest(BaseModel):
    client_event_id: Optional[str] = Field(default=None, max_length=160)
    event_name: str = Field(default="client_event", max_length=160)
    severity: str = Field(default="info", max_length=32)
    source: str = Field(default="react_native", max_length=80)
    scope: Optional[str] = Field(default=None, max_length=120)
    route: Optional[str] = Field(default=None, max_length=240)
    api_path: Optional[str] = Field(default=None, max_length=300)
    status_code: Optional[int] = None
    error_name: Optional[str] = Field(default=None, max_length=160)
    error_message: Optional[str] = Field(default=None, max_length=800)
    message: Optional[str] = Field(default=None, max_length=800)
    app_version: Optional[str] = Field(default=None, max_length=80)
    app_build: Optional[str] = Field(default=None, max_length=80)
    platform: Optional[str] = Field(default=None, max_length=80)
    meta: Dict[str, Any] = Field(default_factory=dict)


class ClientEventResponse(BaseModel):
    status: str = "ok"
    accepted: bool = True
    event_name: str
    severity: str
    event_id: str
    received_at: str
    stored: bool = False
    schema_version: str = CLIENT_EVENT_SCHEMA_VERSION


def _iso_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _truncate(value: Any, limit: int = MAX_TEXT_LEN) -> str:
    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)] + "…"


def _redact_text(value: Any, limit: int = MAX_TEXT_LEN) -> str:
    text = _truncate(value, limit)
    text = _EMAIL_RE.sub("[redacted-email]", text)
    text = _UUID_RE.sub("[redacted-id]", text)
    text = _TOKENISH_RE.sub("[redacted-token]", text)
    return text


def _event_hash(*parts: Any) -> str:
    raw = "|".join(_redact_text(part, 160) for part in parts if part is not None)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _safe_scalar(value: Any, depth: int = 0) -> Any:
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return _redact_text(value)
    if depth >= 2:
        return _redact_text(value)
    if isinstance(value, Mapping):
        out: Dict[str, Any] = {}
        for key, item in list(value.items())[:MAX_META_KEYS]:
            k = _redact_text(key, 120)
            if any(redacted in k.lower() for redacted in REDACTED_KEYS):
                out[k] = "[redacted]"
            else:
                out[k] = _safe_scalar(item, depth + 1)
        return out
    if isinstance(value, (list, tuple)):
        return [_safe_scalar(item, depth + 1) for item in list(value)[:16]]
    return _redact_text(value)


def _sanitize_meta(value: Mapping[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return dict(_safe_scalar(value) or {})


def _normalize_severity(value: Any) -> str:
    severity = str(value or "info").strip().lower()
    if severity in {"debug", "info", "warning", "error", "fatal"}:
        return severity
    return "info"


def _log_level_for_severity(severity: str) -> str:
    if severity in {"fatal", "error"}:
        return "error"
    if severity == "warning":
        return "warning"
    if severity == "debug":
        return "debug"
    return "info"


async def _optional_user_id(authorization: Optional[str]) -> Optional[str]:
    token = _extract_bearer_token(authorization)
    if not token:
        return None
    try:
        return await _resolve_user_id_from_token(token)
    except Exception:
        return None


def sanitize_client_event_payload(
    payload: ClientEventRequest,
    *,
    client_meta: Optional[Mapping[str, Any]] = None,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
    received_at: Optional[str] = None,
) -> Dict[str, Any]:
    client_meta = dict(client_meta or {})
    severity = _normalize_severity(payload.severity)
    event_name = _redact_text(payload.event_name or "client_event", 160) or "client_event"
    event_id = _redact_text(payload.client_event_id, 160) or _event_hash(event_name, payload.scope, payload.api_path, payload.error_name, payload.error_message)
    return {
        "received_at": received_at or _iso_utc(),
        "client_event_id": event_id,
        "event_name": event_name,
        "severity": severity,
        "source": _redact_text(payload.source or "react_native", 80),
        "scope": _redact_text(payload.scope, 120),
        "route": _redact_text(payload.route, 240),
        "api_path": _redact_text(payload.api_path, 300),
        "status_code": payload.status_code,
        "error_name": _redact_text(payload.error_name, 160),
        "error_message": _redact_text(payload.error_message, 800),
        "message": _redact_text(payload.message, 800),
        "app_version": _redact_text(payload.app_version or client_meta.get("app_version"), 80),
        "app_build": _redact_text(payload.app_build or client_meta.get("app_build"), 80),
        "platform": _redact_text(payload.platform or client_meta.get("platform"), 80),
        "user_present": bool(user_id),
        "user_hash": _event_hash("user", user_id) if user_id else None,
        "request_id": _redact_text(request_id, 80),
        "client_meta": _sanitize_meta(client_meta),
        "meta": _sanitize_meta(payload.meta),
    }


def register_client_event_routes(app: FastAPI) -> None:
    @app.post("/ops/client-events", response_model=ClientEventResponse)
    async def receive_client_event(
        payload: ClientEventRequest,
        request: Request,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> ClientEventResponse:
        client_meta = extract_client_meta(request.headers)
        user_id = await _optional_user_id(authorization)
        request_id = getattr(getattr(request, "state", None), "cocolon_request_id", None)
        event_payload = sanitize_client_event_payload(
            payload,
            client_meta=client_meta,
            user_id=user_id,
            request_id=request_id,
        )
        severity = event_payload["severity"]
        level = _log_level_for_severity(severity)
        log_event(logger, "client_event_received", level=level, **event_payload)
        if severity in {"error", "fatal"}:
            log_alert(
                logger,
                "CLIENT_EVENT_ERROR",
                level="error",
                event="client_event_alert",
                message=event_payload.get("error_message") or event_payload.get("message"),
                event_name=event_payload.get("event_name"),
                scope=event_payload.get("scope"),
                api_path=event_payload.get("api_path"),
                status_code=event_payload.get("status_code"),
                platform=event_payload.get("platform"),
            )
        return ClientEventResponse(
            event_name=event_payload["event_name"] or "client_event",
            severity=severity,
            event_id=event_payload["client_event_id"],
            received_at=event_payload["received_at"],
        )


__all__ = [
    "CLIENT_EVENT_SCHEMA_VERSION",
    "ClientEventRequest",
    "ClientEventResponse",
    "redact_client_event_text",
    "register_client_event_routes",
    "sanitize_client_event_payload",
]

# Backward-compatible public alias for tests / future docs.
redact_client_event_text = _redact_text
