from __future__ import annotations

from typing import Literal, Optional

from fastapi import FastAPI, Header, Path, Query

from api_analysis_reads import MyWebHomeSummaryResponse, MyWebWeeklyDaysResponse
from api_analysis_reports import (
    MyWebEnsureRequest,
    MyWebEnsureResponse,
    MyWebReadyReportsResponse,
    MyWebReportDetailResponse,
)
from api_report_reads import MyWebUnreadStatusResponse
from route_compat_delegate import call_registered_route_json


def register_analysis_compat_routes(app: FastAPI) -> None:
    @app.get('/myweb/home-summary', response_model=MyWebHomeSummaryResponse)
    async def compat_myweb_home_summary(
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> MyWebHomeSummaryResponse:
        payload = await call_registered_route_json(
            app,
            path='/analysis/home-summary',
            detail='Legacy /myweb/home-summary compat failed',
            authorization=authorization,
        )
        return MyWebHomeSummaryResponse(**payload)

    @app.post('/myweb/reports/ensure', response_model=MyWebEnsureResponse)
    async def compat_myweb_reports_ensure(
        req: MyWebEnsureRequest,
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> MyWebEnsureResponse:
        payload = await call_registered_route_json(
            app,
            path='/analysis/reports/ensure',
            method='POST',
            detail='Legacy /myweb/reports/ensure compat failed',
            req=req,
            authorization=authorization,
        )
        return MyWebEnsureResponse(**payload)

    @app.get('/myweb/reports/ready', response_model=MyWebReadyReportsResponse)
    async def compat_myweb_reports_ready(
        report_type: Literal['daily', 'weekly', 'monthly'] = 'weekly',
        limit: int = 10,
        offset: int = 0,
        include_body: bool = Query(default=True),
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> MyWebReadyReportsResponse:
        payload = await call_registered_route_json(
            app,
            path='/analysis/reports/ready',
            detail='Legacy /myweb/reports/ready compat failed',
            report_type=report_type,
            limit=limit,
            offset=offset,
            include_body=include_body,
            authorization=authorization,
        )
        return MyWebReadyReportsResponse(**payload)

    @app.get('/myweb/reports/{report_id}', response_model=MyWebReportDetailResponse)
    async def compat_myweb_report_detail(
        report_id: str = Path(..., min_length=1),
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> MyWebReportDetailResponse:
        payload = await call_registered_route_json(
            app,
            path='/analysis/reports/{report_id}',
            detail='Legacy /myweb/reports/{report_id} compat failed',
            report_id=report_id,
            authorization=authorization,
        )
        return MyWebReportDetailResponse(**payload)

    @app.get('/myweb/reports/{report_id}/weekly-days', response_model=MyWebWeeklyDaysResponse)
    async def compat_myweb_report_weekly_days(
        report_id: str = Path(..., min_length=1),
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> MyWebWeeklyDaysResponse:
        payload = await call_registered_route_json(
            app,
            path='/analysis/reports/{report_id}/weekly-days',
            detail='Legacy /myweb/reports/{report_id}/weekly-days compat failed',
            report_id=report_id,
            authorization=authorization,
        )
        return MyWebWeeklyDaysResponse(**payload)

    @app.get('/report-reads/myweb-unread-status', response_model=MyWebUnreadStatusResponse)
    async def compat_myweb_unread_status(
        limit: int = Query(default=1, ge=1, le=10),
        include_self_structure: bool = Query(default=True),
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> MyWebUnreadStatusResponse:
        payload = await call_registered_route_json(
            app,
            path='/report-reads/analysis-unread-status',
            detail='Legacy /report-reads/myweb-unread-status compat failed',
            limit=limit,
            include_self_structure=include_self_structure,
            authorization=authorization,
        )
        return MyWebUnreadStatusResponse(**payload)
