from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional

from fastapi import FastAPI, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field

from api_emotion_submit import _extract_bearer_token, _resolve_user_id_from_token
from client_compat import extract_client_meta

logger = logging.getLogger("api_app_bootstrap")


class AppBootstrapResponse(BaseModel):
    minimum_supported_version: Optional[str] = None
    recommended_version: Optional[str] = None
    maintenance_message: Optional[str] = None
    feature_flags: Dict[str, bool] = Field(default_factory=dict)
    client_meta: Dict[str, Optional[str]] = Field(default_factory=dict)


class AppStartupResponse(AppBootstrapResponse):
    timezone_name: Optional[str] = None
    startup: Dict[str, Any] = Field(default_factory=dict)


def _feature_flags() -> Dict[str, bool]:
    return {
        "account_delete_enabled": True,
        "myweb_mock_enabled": False,
        "today_question_enabled": True,
        "today_question_history_enabled": True,
        "subscription_sales_enabled": (os.getenv("COCOLON_SUBSCRIPTION_SALES_ENABLED") or "true").strip().lower() in {"1", "true", "yes", "on"},
    }


def _bootstrap_payload(*, client_meta: Optional[Mapping[str, Optional[str]]] = None) -> Dict[str, Any]:
    return {
        "minimum_supported_version": (os.getenv("APP_MINIMUM_SUPPORTED_VERSION") or "").strip() or None,
        "recommended_version": (os.getenv("APP_RECOMMENDED_VERSION") or "").strip() or None,
        "maintenance_message": (os.getenv("APP_MAINTENANCE_MESSAGE") or "").strip() or None,
        "feature_flags": _feature_flags(),
        "client_meta": dict(client_meta or {}),
    }


def _iso_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _extract_timezone_name(request: Request, explicit: Optional[str] = None) -> Optional[str]:
    for candidate in (explicit, request.headers.get("X-Timezone-Name"), request.headers.get("X-Timezone"), request.headers.get("Time-Zone")):
        value = str(candidate or "").strip()
        if value:
            return value
    return None


async def _require_user_id(authorization: Optional[str]) -> str:
    access_token = _extract_bearer_token(authorization)
    if not access_token:
        raise HTTPException(status_code=401, detail="Authorization bearer token is required")
    return await _resolve_user_id_from_token(access_token)


def _startup_fallback_payload(
    *,
    user_id: str,
    client_meta: Optional[Mapping[str, Optional[str]]] = None,
    timezone_name: Optional[str] = None,
    detail: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "schema_version": "startup_snapshot.v2",
        "user_id": str(user_id or "").strip(),
        "client_meta": dict(client_meta or {}),
        "generated_at": _iso_utc(),
        "source_versions": {"schema": "startup_snapshot.v2"},
        "flags": {
            "has_any_friends_unread": False,
            "has_any_myweb_unread": False,
            "has_popup_notice": False,
            "today_question_answered": False,
            "has_any_mymodel_unread": False,
            "has_today_question_popup": False,
        },
        "sections": {},
        "errors": {"startup": str(detail or "unavailable")},
        "timezone_name": timezone_name,
    }


def _normalize_startup_payload(payload: Optional[Mapping[str, Any]], *, timezone_name: Optional[str]) -> Dict[str, Any]:
    normalized = dict(payload or {})
    if timezone_name and not normalized.get("timezone_name"):
        normalized["timezone_name"] = timezone_name
    return normalized


async def _build_startup_response(
    request: Request,
    *,
    authorization: Optional[str],
    force_refresh: bool = False,
    timezone_name: Optional[str] = None,
) -> AppStartupResponse:
    client_meta = extract_client_meta(request.headers)
    resolved_timezone_name = _extract_timezone_name(request, timezone_name)
    user_id = await _require_user_id(authorization)

    try:
        from startup_snapshot_store import get_startup_snapshot

        startup_payload = await get_startup_snapshot(
            user_id,
            client_meta=client_meta,
            timezone_name=resolved_timezone_name,
            force_refresh=bool(force_refresh),
        )
    except Exception as exc:
        logger.exception("app startup snapshot build failed: user_id=%s err=%r", user_id, exc)
        startup_payload = _startup_fallback_payload(
            user_id=user_id,
            client_meta=client_meta,
            timezone_name=resolved_timezone_name,
            detail="snapshot_unavailable",
        )

    return AppStartupResponse(
        **_bootstrap_payload(client_meta=client_meta),
        timezone_name=resolved_timezone_name,
        startup=_normalize_startup_payload(startup_payload, timezone_name=resolved_timezone_name),
    )


def register_app_bootstrap_routes(app: FastAPI) -> None:
    @app.get("/app/bootstrap", response_model=AppBootstrapResponse)
    async def get_app_bootstrap(request: Request) -> AppBootstrapResponse:
        client_meta = extract_client_meta(request.headers)
        return AppBootstrapResponse(**_bootstrap_payload(client_meta=client_meta))

    @app.get("/app/startup", response_model=AppStartupResponse)
    async def get_app_startup(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        force_refresh: bool = Query(default=False, description="If true, bypass the cached startup snapshot for this request."),
        timezone_name: Optional[str] = Query(default=None, description="Optional IANA timezone name or offset used for Today Question / Global Summary sections."),
    ) -> AppStartupResponse:
        return await _build_startup_response(
            request,
            authorization=authorization,
            force_refresh=force_refresh,
            timezone_name=timezone_name,
        )
