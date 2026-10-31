"""Shared normal-application owner; private provider settings stay server-side."""
from __future__ import annotations

import asyncio
import os

from emlis_thread_service import Q3_PROFILE
from cocolon_meaning_experience_engine.natural_reply import PROFILE, SelfHostedNaturalReplySource

_initial_tasks = {}


def application_thread_service():
    from emlis_thread_service import EmlisThreadService
    profile = os.environ.get("EMLIS_AI_RESPONSE_PROFILE", "").strip()
    if not profile:
        return EmlisThreadService(runtime_profile=Q3_PROFILE, enforce_application_policy=True)
    source = None
    if profile:
        if profile != PROFILE:
            raise ValueError("unsupported_emlis_response_profile")
        settings = {"endpoint": os.environ.get("EMLIS_NATURAL_REPLY_ENDPOINT", ""),
                    "model": os.environ.get("EMLIS_NATURAL_REPLY_MODEL", ""),
                    "api_key": os.environ.get("EMLIS_NATURAL_REPLY_API_KEY", "")}
        try:
            source = SelfHostedNaturalReplySource(**settings)
        except ValueError:
            # Saved replies remain readable during provider configuration loss.
            # The profile remains selected, so a new write cannot fall back.
            source = None
    return EmlisThreadService(runtime_profile=Q3_PROFILE, enforce_application_policy=True,
                              natural_reply_source=source, response_profile=profile or None)


def schedule_initial_reply(owner, user_id, input_id):
    """Admission and generation share one retained task, outside submit's wait.

    Cross-process duplicate admission is still prevented by SQL CAS; the service
    persists CALL_STARTED before the one provider request. GET never schedules.
    """
    key = (user_id, input_id)
    if key in _initial_tasks:
        return
    task = asyncio.create_task(owner.start(user_id, input_id))
    _initial_tasks[key] = task

    def finished(result):
        if _initial_tasks.get(key) is result:
            del _initial_tasks[key]
        if not result.cancelled():
            # Failure is read through the persisted state. Consume without
            # logging exception text, input, keys, or a provider response.
            result.exception()
    task.add_done_callback(finished)
