from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, Path, Query

from api_follow import (
    FriendNotificationSettingResponse,
    FriendNotificationSettingUpsertBody,
    FriendNotificationSettingsResponse,
    FriendRemoveBody,
    FriendRemoveResponse,
    FriendRequestActionResponse,
    FriendRequestCreateBody,
    FriendRequestCreateResponse,
    FriendUnreadMarkReadBody,
    FriendUnreadMarkReadResponse,
    FriendUnreadStatusResponse,
)
from api_self_structure import (
    MyProfileFollowListResponse,
    MyProfileFollowRequestCancelBody,
    MyProfileFollowStatsResponse,
    MyProfileIncomingFollowRequestsResponse,
    MyProfileLatestEnsureResponse,
    MyProfileLatestStatusResponse,
    MyProfileLinkActionResponse,
    MyProfileLinkBody,
    MyProfileLookupResponse,
    MyProfileMonthlyEnsureBody,
    MyProfileMonthlyEnsureResponse,
    MyProfileOutgoingFollowRequestsResponse,
    MyProfileRemoveFollowerBody,
)
from api_self_structure_reports import (
    SelfStructureReportDetailResponse as MyProfileReportDetailResponse,
    SelfStructureReportHistoryResponse as MyProfileReportHistoryResponse,
)
from route_compat_delegate import call_registered_route_json


def register_relationship_compat_routes(app: FastAPI) -> None:
    @app.get('/myprofile/lookup', response_model=MyProfileLookupResponse)
    async def compat_myprofile_lookup(
        myprofile_code: Optional[str] = Query(default=None, min_length=4, max_length=64),
        connect_code: Optional[str] = Query(default=None, min_length=4, max_length=64),
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> MyProfileLookupResponse:
        payload = await call_registered_route_json(
            app,
            path='/connect/lookup',
            detail='Legacy /myprofile/lookup compat failed',
            myprofile_code=myprofile_code,
            connect_code=connect_code,
            authorization=authorization,
        )
        return MyProfileLookupResponse(**payload)

    @app.post('/myprofile/follow', response_model=MyProfileLinkActionResponse)
    async def compat_myprofile_follow(
        body: MyProfileLinkBody,
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> MyProfileLinkActionResponse:
        payload = await call_registered_route_json(
            app,
            path='/follow/create',
            method='POST',
            detail='Legacy /myprofile/follow compat failed',
            body=body,
            authorization=authorization,
        )
        return MyProfileLinkActionResponse(**payload)

    @app.post('/myprofile/unfollow', response_model=MyProfileLinkActionResponse)
    async def compat_myprofile_unfollow(
        body: MyProfileLinkBody,
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> MyProfileLinkActionResponse:
        payload = await call_registered_route_json(
            app,
            path='/follow/delete',
            method='POST',
            detail='Legacy /myprofile/unfollow compat failed',
            body=body,
            authorization=authorization,
        )
        return MyProfileLinkActionResponse(**payload)

    @app.post('/myprofile/remove-follower', response_model=MyProfileLinkActionResponse)
    async def compat_myprofile_remove_follower(
        body: MyProfileRemoveFollowerBody,
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> MyProfileLinkActionResponse:
        payload = await call_registered_route_json(
            app,
            path='/follow/remove-follower',
            method='POST',
            detail='Legacy /myprofile/remove-follower compat failed',
            body=body,
            authorization=authorization,
        )
        return MyProfileLinkActionResponse(**payload)

    @app.get('/myprofile/follow-stats', response_model=MyProfileFollowStatsResponse)
    async def compat_myprofile_follow_stats(
        target_user_id: str = Query(...),
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> MyProfileFollowStatsResponse:
        payload = await call_registered_route_json(
            app,
            path='/follow/stats',
            detail='Legacy /myprofile/follow-stats compat failed',
            target_user_id=target_user_id,
            authorization=authorization,
        )
        return MyProfileFollowStatsResponse(**payload)

    @app.post('/myprofile/follow-request/cancel')
    async def compat_myprofile_follow_request_cancel(
        body: MyProfileFollowRequestCancelBody,
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> Dict[str, Any]:
        return await call_registered_route_json(
            app,
            path='/follow/request/cancel',
            method='POST',
            detail='Legacy /myprofile/follow-request/cancel compat failed',
            body=body,
            authorization=authorization,
        )

    @app.get('/myprofile/follow-requests/incoming', response_model=MyProfileIncomingFollowRequestsResponse)
    async def compat_myprofile_follow_requests_incoming(
        limit: int = Query(default=100, ge=1, le=300),
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> MyProfileIncomingFollowRequestsResponse:
        payload = await call_registered_route_json(
            app,
            path='/follow/requests/incoming',
            detail='Legacy /myprofile/follow-requests/incoming compat failed',
            limit=limit,
            authorization=authorization,
        )
        return MyProfileIncomingFollowRequestsResponse(**payload)

    @app.get('/myprofile/follow-requests/outgoing', response_model=MyProfileOutgoingFollowRequestsResponse)
    async def compat_myprofile_follow_requests_outgoing(
        limit: int = Query(default=100, ge=1, le=300),
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> MyProfileOutgoingFollowRequestsResponse:
        payload = await call_registered_route_json(
            app,
            path='/follow/requests/outgoing',
            detail='Legacy /myprofile/follow-requests/outgoing compat failed',
            limit=limit,
            authorization=authorization,
        )
        return MyProfileOutgoingFollowRequestsResponse(**payload)

    @app.post('/myprofile/follow-requests/approve')
    async def compat_myprofile_follow_requests_approve(
        body: Dict[str, Any],
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> Dict[str, Any]:
        return await call_registered_route_json(
            app,
            path='/follow/requests/approve',
            method='POST',
            detail='Legacy /myprofile/follow-requests/approve compat failed',
            body=body,
            authorization=authorization,
        )

    @app.post('/myprofile/follow-requests/reject')
    async def compat_myprofile_follow_requests_reject(
        body: Dict[str, Any],
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> Dict[str, Any]:
        return await call_registered_route_json(
            app,
            path='/follow/requests/reject',
            method='POST',
            detail='Legacy /myprofile/follow-requests/reject compat failed',
            body=body,
            authorization=authorization,
        )

    @app.get('/myprofile/follow-list', response_model=MyProfileFollowListResponse)
    async def compat_myprofile_follow_list(
        target_user_id: str = Query(...),
        tab: str = Query(default='followers'),
        limit: int = Query(default=100, ge=1, le=300),
        offset: int = Query(default=0, ge=0),
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> MyProfileFollowListResponse:
        payload = await call_registered_route_json(
            app,
            path='/follow/list',
            detail='Legacy /myprofile/follow-list compat failed',
            target_user_id=target_user_id,
            tab=tab,
            limit=limit,
            offset=offset,
            authorization=authorization,
        )
        return MyProfileFollowListResponse(**payload)

    @app.get('/myprofile/latest/status', response_model=MyProfileLatestStatusResponse)
    async def compat_myprofile_latest_status(
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> MyProfileLatestStatusResponse:
        payload = await call_registered_route_json(
            app,
            path='/self-structure/latest/status',
            detail='Legacy /myprofile/latest/status compat failed',
            authorization=authorization,
        )
        return MyProfileLatestStatusResponse(**payload)

    @app.get('/myprofile/latest', response_model=MyProfileLatestEnsureResponse)
    async def compat_myprofile_latest(
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
        ensure: bool = Query(default=True),
        force: bool = Query(default=False),
        period: Optional[str] = Query(default=None),
        report_mode: Optional[str] = Query(default=None),
    ) -> MyProfileLatestEnsureResponse:
        payload = await call_registered_route_json(
            app,
            path='/self-structure/latest',
            detail='Legacy /myprofile/latest compat failed',
            authorization=authorization,
            ensure=ensure,
            force=force,
            period=period,
            report_mode=report_mode,
        )
        return MyProfileLatestEnsureResponse(**payload)

    @app.post('/myprofile/monthly/ensure', response_model=MyProfileMonthlyEnsureResponse)
    async def compat_myprofile_monthly_ensure(
        body: MyProfileMonthlyEnsureBody,
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> MyProfileMonthlyEnsureResponse:
        payload = await call_registered_route_json(
            app,
            path='/self-structure/monthly/ensure',
            method='POST',
            detail='Legacy /myprofile/monthly/ensure compat failed',
            body=body,
            authorization=authorization,
        )
        return MyProfileMonthlyEnsureResponse(**payload)

    @app.get('/myprofile/reports/history', response_model=MyProfileReportHistoryResponse)
    async def compat_myprofile_reports_history(
        report_type: str = Query(default='monthly'),
        limit: int = Query(default=60, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> MyProfileReportHistoryResponse:
        payload = await call_registered_route_json(
            app,
            path='/self-structure/reports/history',
            detail='Legacy /myprofile/reports/history compat failed',
            report_type=report_type,
            limit=limit,
            offset=offset,
            authorization=authorization,
        )
        return MyProfileReportHistoryResponse(**payload)

    @app.get('/myprofile/reports/{report_id}', response_model=MyProfileReportDetailResponse)
    async def compat_myprofile_reports_detail(
        report_id: str = Path(..., min_length=1),
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> MyProfileReportDetailResponse:
        payload = await call_registered_route_json(
            app,
            path='/self-structure/reports/{report_id}',
            detail='Legacy /myprofile/reports/{report_id} compat failed',
            report_id=report_id,
            authorization=authorization,
        )
        return MyProfileReportDetailResponse(**payload)

    @app.get('/public/profile/by-friend-code')
    async def compat_public_profile_by_friend_code(code: str) -> Dict[str, Any]:
        return await call_registered_route_json(
            app,
            path='/public/profile/by-share-code',
            detail='Legacy /public/profile/by-friend-code compat failed',
            code=code,
        )

    @app.post('/friends/request', response_model=FriendRequestCreateResponse)
    async def compat_friends_request(
        body: FriendRequestCreateBody,
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> FriendRequestCreateResponse:
        payload = await call_registered_route_json(
            app,
            path='/follow/request',
            method='POST',
            detail='Legacy /friends/request compat failed',
            body=body,
            authorization=authorization,
        )
        return FriendRequestCreateResponse(**payload)

    @app.post('/friends/requests/{request_id}/accept', response_model=FriendRequestActionResponse)
    async def compat_friends_request_accept(
        request_id: int = Path(..., ge=1),
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> FriendRequestActionResponse:
        payload = await call_registered_route_json(
            app,
            path='/follow/requests/{request_id}/accept',
            method='POST',
            detail='Legacy /friends/requests/{request_id}/accept compat failed',
            request_id=request_id,
            authorization=authorization,
        )
        return FriendRequestActionResponse(**payload)

    @app.post('/friends/requests/{request_id}/reject', response_model=FriendRequestActionResponse)
    async def compat_friends_request_reject(
        request_id: int = Path(..., ge=1),
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> FriendRequestActionResponse:
        payload = await call_registered_route_json(
            app,
            path='/follow/requests/{request_id}/reject',
            method='POST',
            detail='Legacy /friends/requests/{request_id}/reject compat failed',
            request_id=request_id,
            authorization=authorization,
        )
        return FriendRequestActionResponse(**payload)

    @app.post('/friends/requests/{request_id}/cancel', response_model=FriendRequestActionResponse)
    async def compat_friends_request_cancel(
        request_id: int = Path(..., ge=1),
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> FriendRequestActionResponse:
        payload = await call_registered_route_json(
            app,
            path='/follow/requests/{request_id}/cancel',
            method='POST',
            detail='Legacy /friends/requests/{request_id}/cancel compat failed',
            request_id=request_id,
            authorization=authorization,
        )
        return FriendRequestActionResponse(**payload)

    @app.post('/friends/remove', response_model=FriendRemoveResponse)
    async def compat_friends_remove(
        body: FriendRemoveBody,
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> FriendRemoveResponse:
        payload = await call_registered_route_json(
            app,
            path='/follow/remove',
            method='POST',
            detail='Legacy /friends/remove compat failed',
            body=body,
            authorization=authorization,
        )
        return FriendRemoveResponse(**payload)

    @app.get('/friends/feed')
    async def compat_friends_feed(
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> Dict[str, Any]:
        return await call_registered_route_json(
            app,
            path='/emotion-log/feed',
            detail='Legacy /friends/feed compat failed',
            authorization=authorization,
        )

    @app.get('/friends/unread-status', response_model=FriendUnreadStatusResponse)
    async def compat_friends_unread_status(
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> FriendUnreadStatusResponse:
        payload = await call_registered_route_json(
            app,
            path='/emotion-log/unread-status',
            detail='Legacy /friends/unread-status compat failed',
            authorization=authorization,
        )
        return FriendUnreadStatusResponse(**payload)

    @app.post('/friends/unread/read-feed', response_model=FriendUnreadMarkReadResponse)
    async def compat_friends_read_feed(
        body: Optional[FriendUnreadMarkReadBody] = None,
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> FriendUnreadMarkReadResponse:
        payload = await call_registered_route_json(
            app,
            path='/emotion-log/unread/read-feed',
            method='POST',
            detail='Legacy /friends/unread/read-feed compat failed',
            body=body,
            authorization=authorization,
        )
        return FriendUnreadMarkReadResponse(**payload)

    @app.post('/friends/unread/read-requests', response_model=FriendUnreadMarkReadResponse)
    async def compat_friends_read_requests(
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> FriendUnreadMarkReadResponse:
        payload = await call_registered_route_json(
            app,
            path='/follow/requests/read',
            method='POST',
            detail='Legacy /friends/unread/read-requests compat failed',
            authorization=authorization,
        )
        return FriendUnreadMarkReadResponse(**payload)

    @app.get('/friends/notification-settings', response_model=FriendNotificationSettingsResponse)
    async def compat_friends_notification_settings(
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> FriendNotificationSettingsResponse:
        payload = await call_registered_route_json(
            app,
            path='/emotion-notifications/settings',
            detail='Legacy /friends/notification-settings compat failed',
            authorization=authorization,
        )
        return FriendNotificationSettingsResponse(**payload)

    @app.post('/friends/notification-settings/{friend_user_id}', response_model=FriendNotificationSettingResponse)
    async def compat_friends_notification_setting_upsert(
        body: FriendNotificationSettingUpsertBody,
        friend_user_id: str = Path(..., min_length=1, max_length=128),
        authorization: Optional[str] = Header(default=None, alias='Authorization'),
    ) -> FriendNotificationSettingResponse:
        payload = await call_registered_route_json(
            app,
            path='/emotion-notifications/settings/{friend_user_id}',
            method='POST',
            detail='Legacy /friends/notification-settings/{friend_user_id} compat failed',
            body=body,
            friend_user_id=friend_user_id,
            authorization=authorization,
        )
        return FriendNotificationSettingResponse(**payload)
