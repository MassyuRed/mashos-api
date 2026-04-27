# -*- coding: utf-8 -*-
"""Legacy friend feed enqueue compat facade.

The current owner is ``astor_emotion_log_feed_enqueue``. This module is kept
for legacy imports and queue compatibility names during the rename-safe phase.
"""

from __future__ import annotations

from astor_emotion_log_feed_enqueue import (
    ASTOR_EMOTION_LOG_FEED_DEBOUNCE_SECONDS,
    ASTOR_EMOTION_LOG_FEED_ENQUEUE_ENABLED,
    ASTOR_FRIEND_FEED_DEBOUNCE_SECONDS,
    ASTOR_FRIEND_FEED_ENQUEUE_ENABLED,
    ASTOR_WORKER_QUEUE_ENABLED,
    EMOTION_LOG_FEED_REFRESH_JOB_KEY_PREFIX,
    EMOTION_LOG_FEED_REFRESH_JOB_TYPE,
    FRIEND_FEED_REFRESH_JOB_KEY_PREFIX,
    FRIEND_FEED_REFRESH_JOB_TYPE,
    enqueue_emotion_log_feed_refresh,
    enqueue_emotion_log_feed_refresh_many,
    enqueue_friend_feed_refresh,
    enqueue_friend_feed_refresh_many,
)

__all__ = [
    "FRIEND_FEED_REFRESH_JOB_TYPE",
    "FRIEND_FEED_REFRESH_JOB_KEY_PREFIX",
    "EMOTION_LOG_FEED_REFRESH_JOB_TYPE",
    "EMOTION_LOG_FEED_REFRESH_JOB_KEY_PREFIX",
    "ASTOR_WORKER_QUEUE_ENABLED",
    "ASTOR_FRIEND_FEED_ENQUEUE_ENABLED",
    "ASTOR_FRIEND_FEED_DEBOUNCE_SECONDS",
    "ASTOR_EMOTION_LOG_FEED_ENQUEUE_ENABLED",
    "ASTOR_EMOTION_LOG_FEED_DEBOUNCE_SECONDS",
    "enqueue_emotion_log_feed_refresh",
    "enqueue_emotion_log_feed_refresh_many",
    "enqueue_friend_feed_refresh",
    "enqueue_friend_feed_refresh_many",
]
