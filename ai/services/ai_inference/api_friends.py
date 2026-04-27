# -*- coding: utf-8 -*-
"""Legacy Friends aggregate compat facade.

Runtime body now lives in the current Follow / EmotionLog / EmotionNotification
owners. This module forwards legacy imports while DB/table names remain
friend-compatible until the DB rename phase.
"""

from __future__ import annotations

import sys
import types

import api_follow as _follow
import api_emotion_log as _emotion_log
import api_emotion_notification_settings as _emotion_notifications

FriendRequestCreateBody = _follow.FriendRequestCreateBody
FriendRequestCreateResponse = _follow.FriendRequestCreateResponse
FriendRequestActionResponse = _follow.FriendRequestActionResponse
FriendRemoveBody = _follow.FriendRemoveBody
FriendRemoveResponse = _follow.FriendRemoveResponse
FriendNotificationSettingUpsertBody = _follow.FriendNotificationSettingUpsertBody
FriendNotificationSettingItem = _follow.FriendNotificationSettingItem
FriendNotificationSettingResponse = _follow.FriendNotificationSettingResponse
FriendNotificationSettingsResponse = _follow.FriendNotificationSettingsResponse
FriendUnreadStatusResponse = _follow.FriendUnreadStatusResponse
FriendUnreadMarkReadResponse = _follow.FriendUnreadMarkReadResponse
FriendUnreadMarkReadBody = _follow.FriendUnreadMarkReadBody
FollowRequestCreateBody = _follow.FollowRequestCreateBody
FollowRequestCreateResponse = _follow.FollowRequestCreateResponse
FollowRequestActionResponse = _follow.FollowRequestActionResponse
FollowRemoveBody = _follow.FollowRemoveBody
FollowRemoveResponse = _follow.FollowRemoveResponse
FollowRequestsReadResponse = _follow.FollowRequestsReadResponse
get_friend_unread_status_payload_for_user = _follow.get_friend_unread_status_payload_for_user
get_emotion_log_unread_status_payload_for_user = _follow.get_emotion_log_unread_status_payload_for_user


def register_follow_routes(app):
    return _follow.register_follow_routes(app)


def register_emotion_log_routes(app):
    return _emotion_log.register_emotion_log_routes(app)


def register_emotion_notification_routes(app):
    return _emotion_notifications.register_emotion_notification_settings_routes(app)


def register_friend_routes(app):
    register_follow_routes(app)
    register_emotion_log_routes(app)
    register_emotion_notification_routes(app)


_TARGET_MODULES = (_follow, _emotion_log, _emotion_notifications)


class _CompatModule(types.ModuleType):
    def __getattr__(self, name: str):
        for module in _TARGET_MODULES:
            try:
                return getattr(module, name)
            except AttributeError:
                continue
        raise AttributeError(name)

    def __setattr__(self, name: str, value):
        if not name.startswith("__"):
            for module in _TARGET_MODULES:
                if hasattr(module, name):
                    try:
                        setattr(module, name, value)
                    except Exception:
                        pass
        return super().__setattr__(name, value)


sys.modules[__name__].__class__ = _CompatModule


def __getattr__(name: str):
    for module in _TARGET_MODULES:
        try:
            return getattr(module, name)
        except AttributeError:
            continue
    raise AttributeError(name)


__all__ = [
    "FriendRequestCreateBody",
    "FriendRequestCreateResponse",
    "FriendRequestActionResponse",
    "FriendRemoveBody",
    "FriendRemoveResponse",
    "FriendNotificationSettingUpsertBody",
    "FriendNotificationSettingItem",
    "FriendNotificationSettingResponse",
    "FriendNotificationSettingsResponse",
    "FriendUnreadStatusResponse",
    "FriendUnreadMarkReadResponse",
    "FriendUnreadMarkReadBody",
    "FollowRequestCreateBody",
    "FollowRequestCreateResponse",
    "FollowRequestActionResponse",
    "FollowRemoveBody",
    "FollowRemoveResponse",
    "FollowRequestsReadResponse",
    "get_friend_unread_status_payload_for_user",
    "get_emotion_log_unread_status_payload_for_user",
    "register_follow_routes",
    "register_emotion_log_routes",
    "register_emotion_notification_routes",
    "register_friend_routes",
]
