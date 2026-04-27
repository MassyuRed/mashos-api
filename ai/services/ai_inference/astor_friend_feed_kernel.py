# -*- coding: utf-8 -*-
"""Legacy friend feed kernel compat facade.

The current owner is ``astor_emotion_log_feed_kernel``. This module is kept for
legacy imports while source tables and queue names remain DB-compatible.
"""

from __future__ import annotations

from astor_emotion_log_feed_kernel import (
    EMOTION_LOG_FEED_MAX_ITEMS,
    EMOTION_LOG_FEED_SOURCE_TABLE,
    EMOTION_LOG_FEED_TIMEZONE,
    EMOTION_LOG_FEED_VERSION,
    FRIEND_FEED_MAX_ITEMS,
    FRIEND_FEED_SOURCE_TABLE,
    FRIEND_FEED_TIMEZONE,
    FRIEND_FEED_VERSION,
    generate_emotion_log_feed,
    generate_friend_feed,
    generate_multiple_emotion_log_feeds,
    generate_multiple_friend_feeds,
)

__all__ = [
    "FRIEND_FEED_SOURCE_TABLE",
    "FRIEND_FEED_TIMEZONE",
    "FRIEND_FEED_MAX_ITEMS",
    "FRIEND_FEED_VERSION",
    "EMOTION_LOG_FEED_SOURCE_TABLE",
    "EMOTION_LOG_FEED_TIMEZONE",
    "EMOTION_LOG_FEED_MAX_ITEMS",
    "EMOTION_LOG_FEED_VERSION",
    "generate_friend_feed",
    "generate_multiple_friend_feeds",
    "generate_emotion_log_feed",
    "generate_multiple_emotion_log_feeds",
]
