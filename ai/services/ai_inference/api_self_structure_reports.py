from __future__ import annotations

"""Current Self Structure report read API entrypoint.

This module owns the current-vocabulary Self Structure report history/detail
route definitions. Legacy MyProfile-named modules may delegate here during the
rename-safe phase.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, Path, Query
from pydantic import BaseModel, Field

from api_account_visibility import _require_user_id
from report_artifact_read_service import get_detail, list_history


class SelfStructureReportHistoryItem(BaseModel):
    id: str
    report_type: str
    title: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    generated_at: Optional[str] = None
    updated_at: Optional[str] = None


class SelfStructureReportHistoryResponse(BaseModel):
    status: str = "ok"
    items: List[SelfStructureReportHistoryItem] = Field(default_factory=list)
    limit: int = 60
    offset: int = 0
    has_more: bool = False
    next_offset: Optional[int] = None
    subscription_tier: str = "free"


class SelfStructureReportDetailItem(SelfStructureReportHistoryItem):
    content_text: Optional[str] = None
    content_json: Dict[str, Any] = Field(default_factory=dict)


class SelfStructureReportDetailResponse(BaseModel):
    status: str = "ok"
    item: SelfStructureReportDetailItem


def register_self_structure_report_routes(app: FastAPI) -> None:
    @app.get("/self-structure/reports/history", response_model=SelfStructureReportHistoryResponse)
    async def get_self_structure_report_history(
        report_type: str = Query(default="monthly"),
        limit: int = Query(default=60, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> SelfStructureReportHistoryResponse:
        """Current owner for Self Structure report history."""
        me = await _require_user_id(authorization)
        payload = await list_history(
            user_id=me,
            family="self_structure",
            report_type=str(report_type or "monthly"),
            limit=int(limit or 60),
            offset=int(offset or 0),
            now_utc=datetime.now(timezone.utc),
        )
        return SelfStructureReportHistoryResponse(**payload)

    @app.get("/self-structure/reports/{report_id}", response_model=SelfStructureReportDetailResponse)
    async def get_self_structure_report_detail(
        report_id: str = Path(..., min_length=1),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> SelfStructureReportDetailResponse:
        """Current owner for Self Structure report detail."""
        me = await _require_user_id(authorization)
        payload = await get_detail(
            user_id=me,
            family="self_structure",
            report_id=str(report_id or "").strip(),
            now_utc=datetime.now(timezone.utc),
        )
        return SelfStructureReportDetailResponse(**payload)


__all__ = [
    "SelfStructureReportHistoryItem",
    "SelfStructureReportHistoryResponse",
    "SelfStructureReportDetailItem",
    "SelfStructureReportDetailResponse",
    "register_self_structure_report_routes",
]
