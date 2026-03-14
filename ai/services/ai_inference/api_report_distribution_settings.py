# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel

from active_users_store import touch_active_user
from api_emotion_submit import _extract_bearer_token, _resolve_user_id_from_token
from report_distribution_settings_store import ReportDistributionSettingsStore

logger = logging.getLogger("report_distribution_settings_api")
store = ReportDistributionSettingsStore()


class ReportDistributionSettingsResponse(BaseModel):
    notification_enabled: bool = True
    delivery_time_local: str = "00:00"
    timezone_name: str = "Asia/Tokyo"


class ReportDistributionSettingsPatchRequest(BaseModel):
    notification_enabled: Optional[bool] = None
    delivery_time_local: Optional[str] = None
    timezone_name: Optional[str] = None


async def _require_user_id(authorization: Optional[str]) -> str:
    token = _extract_bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    uid = await _resolve_user_id_from_token(token)
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        await touch_active_user(uid)
    except Exception:
        logger.exception("report_distribution_settings: touch_active_user failed")
    return uid


def register_report_distribution_settings_routes(app: FastAPI) -> None:
    @app.get("/report-distribution/settings", response_model=ReportDistributionSettingsResponse)
    async def report_distribution_settings_read(
        timezone_name: Optional[str] = Query(default=None),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> ReportDistributionSettingsResponse:
        uid = await _require_user_id(authorization)
        settings = await store.get_or_create_user_settings(uid, timezone_name=timezone_name)
        return ReportDistributionSettingsResponse(**settings)

    @app.patch("/report-distribution/settings", response_model=ReportDistributionSettingsResponse)
    async def report_distribution_settings_patch(
        body: ReportDistributionSettingsPatchRequest,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> ReportDistributionSettingsResponse:
        uid = await _require_user_id(authorization)
        settings = await store.patch_user_settings(
            uid,
            notification_enabled=body.notification_enabled,
            delivery_time_local=body.delivery_time_local,
            timezone_name=body.timezone_name,
        )
        return ReportDistributionSettingsResponse(**settings)
