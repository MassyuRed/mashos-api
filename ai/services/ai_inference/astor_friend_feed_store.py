# -*- coding: utf-8 -*-
"""Legacy friend feed store compat facade.

The current owner is ``astor_emotion_log_feed_store``. This module is kept for
legacy imports while DB physical table names remain friend-feed compatible.
"""

from __future__ import annotations

from astor_emotion_log_feed_store import (
    ALLOWED_STATUSES,
    ALLOWED_STRENGTHS,
    EMOTION_LOG_FEED_MAX_ITEMS,
    EMOTION_LOG_FEED_SUMMARIES_TABLE,
    EMOTION_LOG_FEED_VERSION,
    FRIEND_FEED_MAX_ITEMS,
    FRIEND_FEED_SUMMARIES_TABLE,
    FRIEND_FEED_VERSION,
    STATUS_DRAFT,
    STATUS_FAILED,
    STATUS_READY,
    build_emotion_log_feed_source_hash,
    build_friend_feed_source_hash,
    fail_emotion_log_feed_summary,
    fail_friend_feed_summary,
    fetch_latest_emotion_log_feed_summary,
    fetch_latest_friend_feed_summary,
    fetch_latest_ready_emotion_log_feed_summary,
    fetch_latest_ready_friend_feed_summary,
    normalize_emotion_log_feed_payload,
    normalize_friend_feed_payload,
    promote_emotion_log_feed_summary,
    promote_friend_feed_summary,
    select_emotion_log_feed_items,
    select_friend_feed_items,
    upsert_emotion_log_feed_draft,
    upsert_friend_feed_draft,
)

__all__ = [
    "FRIEND_FEED_SUMMARIES_TABLE",
    "EMOTION_LOG_FEED_SUMMARIES_TABLE",
    "FRIEND_FEED_VERSION",
    "EMOTION_LOG_FEED_VERSION",
    "STATUS_DRAFT",
    "STATUS_READY",
    "STATUS_FAILED",
    "ALLOWED_STATUSES",
    "FRIEND_FEED_MAX_ITEMS",
    "EMOTION_LOG_FEED_MAX_ITEMS",
    "ALLOWED_STRENGTHS",
    "normalize_friend_feed_payload",
    "build_friend_feed_source_hash",
    "upsert_friend_feed_draft",
    "fetch_latest_friend_feed_summary",
    "fetch_latest_ready_friend_feed_summary",
    "promote_friend_feed_summary",
    "fail_friend_feed_summary",
    "select_friend_feed_items",
    "normalize_emotion_log_feed_payload",
    "build_emotion_log_feed_source_hash",
    "upsert_emotion_log_feed_draft",
    "fetch_latest_emotion_log_feed_summary",
    "fetch_latest_ready_emotion_log_feed_summary",
    "promote_emotion_log_feed_summary",
    "fail_emotion_log_feed_summary",
    "select_emotion_log_feed_items",
]
