from __future__ import annotations

from typing import Any, Optional

from fastapi import FastAPI, Header, Path, Query, Request

from api_emotion_piece import (
    EmotionReflectionCancelRequest,
    EmotionReflectionCancelResponse,
    EmotionReflectionPreviewRequest,
    EmotionReflectionPreviewResponse,
    EmotionReflectionPublishRequest,
    EmotionReflectionPublishResponse,
    EmotionReflectionQuotaResponse,
)
from api_piece_runtime import (
    QnaDetailResponse,
    QnaEchoesDeleteRequest,
    QnaEchoesDeleteResponse,
    QnaEchoesHistoryResponse,
    QnaEchoesSubmitRequest,
    QnaEchoesSubmitResponse,
    QnaListResponse,
    QnaResonanceRequest,
    QnaResonanceResponse,
    QnaSavedReflectionsResponse,
    QnaUnreadResponse,
    QnaUnreadStatusResponse,
    QnaViewRequest,
    QnaViewResponse,
)
from api_nexus import (
    NexusRecommendUsersResponse,
    NexusReflectionDetailResponse,
    NexusReflectionResponse,
    NexusReflectionsUnreadStatusResponse,
)
from route_compat_delegate import call_registered_route_json


def register_piece_compat_routes(app: FastAPI) -> None:
    @app.get('/emotion/reflection/quota', response_model=EmotionReflectionQuotaResponse)
    async def compat_emotion_reflection_quota(
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> EmotionReflectionQuotaResponse:
        payload = await call_registered_route_json(
            app,
            path='/emotion/piece/quota',
            detail='Legacy /emotion/reflection/quota compat failed',
            authorization=authorization,
        )
        return EmotionReflectionQuotaResponse(**payload)

    @app.post('/emotion/reflection/preview', response_model=EmotionReflectionPreviewResponse)
    async def compat_emotion_reflection_preview(
        request: Request,
        payload: EmotionReflectionPreviewRequest,
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> EmotionReflectionPreviewResponse:
        result = await call_registered_route_json(
            app,
            path='/emotion/piece/preview',
            method='POST',
            detail='Legacy /emotion/reflection/preview compat failed',
            request=request,
            payload=payload,
            authorization=authorization,
        )
        return EmotionReflectionPreviewResponse(**result)

    @app.post('/emotion/reflection/publish', response_model=EmotionReflectionPublishResponse)
    async def compat_emotion_reflection_publish(
        body: EmotionReflectionPublishRequest,
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> EmotionReflectionPublishResponse:
        payload = await call_registered_route_json(
            app,
            path='/emotion/piece/publish',
            method='POST',
            detail='Legacy /emotion/reflection/publish compat failed',
            body=body,
            authorization=authorization,
        )
        return EmotionReflectionPublishResponse(**payload)

    @app.post('/emotion/reflection/cancel', response_model=EmotionReflectionCancelResponse)
    async def compat_emotion_reflection_cancel(
        body: EmotionReflectionCancelRequest,
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> EmotionReflectionCancelResponse:
        payload = await call_registered_route_json(
            app,
            path='/emotion/piece/cancel',
            method='POST',
            detail='Legacy /emotion/reflection/cancel compat failed',
            body=body,
            authorization=authorization,
        )
        return EmotionReflectionCancelResponse(**payload)

    @app.get('/nexus/reflections', response_model=NexusReflectionResponse)
    async def compat_nexus_reflections(
        sort: str = Query(default='latest'),
        limit: int = Query(default=20, ge=1, le=100),
        user_id: Optional[str] = Query(default=None),
        following_only: bool = Query(default=True),
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> NexusReflectionResponse:
        payload = await call_registered_route_json(
            app,
            path='/nexus/pieces',
            detail='Legacy /nexus/reflections compat failed',
            sort=sort,
            limit=limit,
            user_id=user_id,
            following_only=following_only,
            authorization=authorization,
        )
        return NexusReflectionResponse(**payload)

    @app.get('/nexus/reflections/unread-status', response_model=NexusReflectionsUnreadStatusResponse)
    async def compat_nexus_reflections_unread_status(
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> NexusReflectionsUnreadStatusResponse:
        payload = await call_registered_route_json(
            app,
            path='/nexus/pieces/unread-status',
            detail='Legacy /nexus/reflections/unread-status compat failed',
            authorization=authorization,
        )
        return NexusReflectionsUnreadStatusResponse(**payload)

    @app.get('/nexus/reflections/{q_instance_id}', response_model=NexusReflectionDetailResponse)
    async def compat_nexus_reflection_detail(
        q_instance_id: str,
        mark_viewed: bool = Query(default=False),
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> NexusReflectionDetailResponse:
        payload = await call_registered_route_json(
            app,
            path='/nexus/pieces/{q_instance_id}',
            detail='Legacy /nexus/reflections/{q_instance_id} compat failed',
            q_instance_id=q_instance_id,
            mark_viewed=mark_viewed,
            authorization=authorization,
        )
        return NexusReflectionDetailResponse(**payload)

    @app.get('/nexus/history/echoes')
    async def compat_nexus_history_echoes(
        limit: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> Any:
        return await call_registered_route_json(
            app,
            path='/nexus/history/resonances',
            detail='Legacy /nexus/history/echoes compat failed',
            limit=limit,
            offset=offset,
            authorization=authorization,
        )

    @app.get('/mymodel/recommend/users', response_model=NexusRecommendUsersResponse)
    async def compat_mymodel_recommend_users(
        limit: int = Query(default=8, ge=1, le=100),
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> NexusRecommendUsersResponse:
        payload = await call_registered_route_json(
            app,
            path='/nexus/recommend/users',
            detail='Legacy /mymodel/recommend/users compat failed',
            limit=limit,
            authorization=authorization,
        )
        return NexusRecommendUsersResponse(**payload)

    @app.get('/mymodel/qna/list', response_model=QnaListResponse)
    async def compat_mymodel_qna_list(
        target_user_id: Optional[str] = Query(default=None),
        sort: str = Query(default='newest'),
        metric: str = Query(default='views'),
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> QnaListResponse:
        payload = await call_registered_route_json(
            app,
            path='/piece/library',
            detail='Legacy /mymodel/qna/list compat failed',
            target_user_id=target_user_id,
            sort=sort,
            metric=metric,
            authorization=authorization,
        )
        return QnaListResponse(**payload)

    @app.get('/mymodel/qna/unread', response_model=QnaUnreadResponse)
    async def compat_mymodel_qna_unread(
        target_user_id: Optional[str] = Query(default=None),
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> QnaUnreadResponse:
        payload = await call_registered_route_json(
            app,
            path='/piece/unread',
            detail='Legacy /mymodel/qna/unread compat failed',
            target_user_id=target_user_id,
            authorization=authorization,
        )
        return QnaUnreadResponse(**payload)

    @app.get('/mymodel/qna/unread-status', response_model=QnaUnreadStatusResponse)
    async def compat_mymodel_qna_unread_status(
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> QnaUnreadStatusResponse:
        payload = await call_registered_route_json(
            app,
            path='/piece/unread-status',
            detail='Legacy /mymodel/qna/unread-status compat failed',
            authorization=authorization,
        )
        return QnaUnreadStatusResponse(**payload)

    @app.get('/mymodel/qna/detail', response_model=QnaDetailResponse)
    async def compat_mymodel_qna_detail(
        q_instance_id: str = Query(...),
        mark_viewed: bool = Query(default=False),
        include_my_discovery_latest: bool = Query(default=False),
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> QnaDetailResponse:
        payload = await call_registered_route_json(
            app,
            path='/piece/detail',
            detail='Legacy /mymodel/qna/detail compat failed',
            q_instance_id=q_instance_id,
            mark_viewed=mark_viewed,
            include_my_discovery_latest=include_my_discovery_latest,
            authorization=authorization,
        )
        return QnaDetailResponse(**payload)

    @app.post('/mymodel/qna/view', response_model=QnaViewResponse)
    async def compat_mymodel_qna_view(
        req: QnaViewRequest,
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> QnaViewResponse:
        payload = await call_registered_route_json(
            app,
            path='/piece/view',
            method='POST',
            detail='Legacy /mymodel/qna/view compat failed',
            req=req,
            authorization=authorization,
        )
        return QnaViewResponse(**payload)

    @app.post('/mymodel/qna/resonance', response_model=QnaResonanceResponse)
    async def compat_mymodel_qna_resonance(
        req: QnaResonanceRequest,
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> QnaResonanceResponse:
        payload = await call_registered_route_json(
            app,
            path='/piece/resonance',
            method='POST',
            detail='Legacy /mymodel/qna/resonance compat failed',
            req=req,
            authorization=authorization,
        )
        return QnaResonanceResponse(**payload)

    @app.get('/mymodel/qna/echoes/reflections', response_model=QnaSavedReflectionsResponse)
    async def compat_mymodel_qna_echoes_reflections(
        order: str = Query(default='newest'),
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> QnaSavedReflectionsResponse:
        payload = await call_registered_route_json(
            app,
            path='/piece/resonances/pieces',
            detail='Legacy /mymodel/qna/echoes/reflections compat failed',
            order=order,
            limit=limit,
            offset=offset,
            authorization=authorization,
        )
        return QnaSavedReflectionsResponse(**payload)

    @app.post('/mymodel/qna/echoes/submit', response_model=QnaEchoesSubmitResponse)
    async def compat_mymodel_qna_echoes_submit(
        req: QnaEchoesSubmitRequest,
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> QnaEchoesSubmitResponse:
        payload = await call_registered_route_json(
            app,
            path='/piece/resonances/submit',
            method='POST',
            detail='Legacy /mymodel/qna/echoes/submit compat failed',
            req=req,
            authorization=authorization,
        )
        return QnaEchoesSubmitResponse(**payload)

    @app.post('/mymodel/qna/echoes/delete', response_model=QnaEchoesDeleteResponse)
    async def compat_mymodel_qna_echoes_delete(
        req: QnaEchoesDeleteRequest,
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> QnaEchoesDeleteResponse:
        payload = await call_registered_route_json(
            app,
            path='/piece/resonances/delete',
            method='POST',
            detail='Legacy /mymodel/qna/echoes/delete compat failed',
            req=req,
            authorization=authorization,
        )
        return QnaEchoesDeleteResponse(**payload)

    @app.get('/mymodel/qna/echoes/history', response_model=QnaEchoesHistoryResponse)
    async def compat_mymodel_qna_echoes_history(
        q_instance_id: str = Query(...),
        q_key: Optional[str] = Query(default=None),
        limit: Optional[int] = Query(default=None),
        offset: Optional[int] = Query(default=None),
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> QnaEchoesHistoryResponse:
        payload = await call_registered_route_json(
            app,
            path='/piece/resonances/history',
            detail='Legacy /mymodel/qna/echoes/history compat failed',
            q_instance_id=q_instance_id,
            q_key=q_key,
            limit=limit,
            offset=offset,
            authorization=authorization,
        )
        return QnaEchoesHistoryResponse(**payload)
