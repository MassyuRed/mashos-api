# -*- coding: utf-8 -*-
from __future__ import annotations

"""Reader adapters used by EmlisAI.

This module centralizes the context-service dependency on read-side payload builders.
The current implementation keeps backward-compatible imports under one boundary so
EmlisAI does not directly reach into route modules anymore.
"""

from typing import Any, Dict


async def get_input_summary_for_emlis_ai(user_id: str) -> Dict[str, Any]:
    try:
        from api_input_summary import get_input_summary_payload_for_user

        return await get_input_summary_payload_for_user(user_id)
    except Exception:
        return {}


async def get_myweb_home_summary_for_emlis_ai(user_id: str) -> Dict[str, Any]:
    try:
        from api_myweb_reads import get_myweb_home_summary_payload_for_user

        return await get_myweb_home_summary_payload_for_user(user_id)
    except Exception:
        return {}
