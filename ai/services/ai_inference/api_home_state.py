from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import FastAPI, Header, Query, Request
from pydantic import BaseModel, Field

from api_emotion_piece import EmotionPieceQuotaResponse
from api_global_summary import GlobalSummaryResponse
from api_input_summary import InputSummaryResponse
from api_notice import NoticeCurrentResponse
from api_today_question import TodayQuestionCurrentResponse
from client_compat import extract_client_meta
from home_gateway.emotion_submit_service import resolve_authenticated_user_id
from home_gateway.read_model_service import get_home_state


class HomeStatePopupCandidate(BaseModel):
    kind: str
    notice_id: Optional[str] = None
    service_day_key: Optional[str] = None
    question_id: Optional[str] = None


class HomeStateSections(BaseModel):
    input_summary: InputSummaryResponse
    global_summary: GlobalSummaryResponse
    notices_current: NoticeCurrentResponse
    today_question_current: TodayQuestionCurrentResponse
    emotion_reflection_quota: EmotionPieceQuotaResponse


class HomeStateResponse(BaseModel):
    status: str = Field(default="ok")
    user_id: str
    generated_at: str
    service_day_key: str
    source_versions: Dict[str, str] = Field(default_factory=dict)
    popup_candidates: List[HomeStatePopupCandidate] = Field(default_factory=list)
    notice_popup_notice_id: Optional[str] = None
    sections: HomeStateSections
    errors: Dict[str, str] = Field(default_factory=dict)


def register_home_state_routes(app: FastAPI) -> None:
    @app.get("/home/state", response_model=HomeStateResponse)
    async def home_state(
        request: Request,
        timezone_name: Optional[str] = Query(default=None),
        force_refresh: bool = Query(default=False),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> HomeStateResponse:
        user_id = await resolve_authenticated_user_id(authorization=authorization)
        payload = await get_home_state(
            user_id,
            client_meta=extract_client_meta(request.headers),
            timezone_name=timezone_name,
            force_refresh=bool(force_refresh),
        )
        return HomeStateResponse(**payload)
