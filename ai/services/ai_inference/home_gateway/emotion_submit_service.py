from __future__ import annotations

import emotion_submit_service as _legacy_service


def normalize_submission_payload(*args, **kwargs):
    return _legacy_service.normalize_submission_payload(*args, **kwargs)


async def persist_emotion_submission(*args, **kwargs):
    return await _legacy_service.persist_emotion_submission(*args, **kwargs)


async def resolve_authenticated_user_id(*args, **kwargs):
    return await _legacy_service.resolve_authenticated_user_id(*args, **kwargs)


__all__ = [
    "normalize_submission_payload",
    "persist_emotion_submission",
    "resolve_authenticated_user_id",
]
