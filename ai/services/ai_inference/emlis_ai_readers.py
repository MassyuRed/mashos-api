# -*- coding: utf-8 -*-
from __future__ import annotations

"""Meaning-layer readers used by EmlisAI.

EmlisAI should depend on stable read contracts, not route modules.
This boundary is intentionally thin so context collection only sees canonical
reader functions for input status and analysis summary artifacts.
"""

from typing import Any, Dict

from analysis_summary_reader import get_myweb_home_summary_from_artifacts
from input_summary_reader import get_input_summary_snapshot


async def get_input_summary_for_emlis_ai(user_id: str) -> Dict[str, Any]:
    try:
        return await get_input_summary_snapshot(user_id)
    except Exception:
        return {}


async def get_myweb_home_summary_for_emlis_ai(user_id: str) -> Dict[str, Any]:
    try:
        return await get_myweb_home_summary_from_artifacts(user_id)
    except Exception:
        return {}
