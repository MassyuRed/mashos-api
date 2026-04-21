from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, Path, Query
from pydantic import BaseModel, Field

from api_account_visibility import _require_user_id
from report_artifact_read_service import get_detail, list_history


class MyProfileReportHistoryItem(BaseModel):
    id: str
    report_type: str
    title: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    generated_at: Optional[str] = None
    updated_at: Optional[str] = None


class MyProfileReportHistoryResponse(BaseModel):
    status: str = "ok"
    items: List[MyProfileReportHistoryItem] = Field(default_factory=list)
    limit: int = 60
    offset: int = 0
    has_more: bool = False
    next_offset: Optional[int] = None
    subscription_tier: str = "free"


class MyProfileReportDetailItem(MyProfileReportHistoryItem):
    content_text: Optional[str] = None
    content_json: Dict[str, Any] = Field(default_factory=dict)


class MyProfileReportDetailResponse(BaseModel):
    status: str = "ok"
    item: MyProfileReportDetailItem


def register_myprofile_report_read_routes(app: FastAPI) -> None:
    @app.get("/myprofile/reports/history", response_model=MyProfileReportHistoryResponse)
    async def get_myprofile_report_history(
        report_type: str = Query(default="monthly"),
        limit: int = Query(default=60, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> MyProfileReportHistoryResponse:
        """Thin façade over the canonical report artifact read service."""
        me = await _require_user_id(authorization)
        payload = await list_history(
            user_id=me,
            family="self_structure",
            report_type=str(report_type or "monthly"),
            limit=int(limit or 60),
            offset=int(offset or 0),
            now_utc=datetime.now(timezone.utc),
        )
        return MyProfileReportHistoryResponse(**payload)

    @app.get("/myprofile/reports/{report_id}", response_model=MyProfileReportDetailResponse)
    async def get_myprofile_report_detail(
        report_id: str = Path(..., min_length=1),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> MyProfileReportDetailResponse:
        """Thin façade over the canonical report artifact read service."""
        me = await _require_user_id(authorization)
        payload = await get_detail(
            user_id=me,
            family="self_structure",
            report_id=str(report_id or "").strip(),
            now_utc=datetime.now(timezone.utc),
        )
        return MyProfileReportDetailResponse(**payload)
