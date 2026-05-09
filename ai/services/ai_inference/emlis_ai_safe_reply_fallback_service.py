# -*- coding: utf-8 -*-
from __future__ import annotations

"""Retired fixed fallback for EmlisAI observations.

The new EmlisAI contract is fail-closed: when the observation cannot pass the
reader, grounding, template/echo and safety gates, no Emlis observation body is
returned.  This module remains only so older imports do not break; it must not
produce user-facing fixed observation text.
"""

from typing import Any


def build_safe_understanding_fallback(*_: Any, **__: Any) -> str:
    """Return no observation text.

    Fixed fallback sentences are prohibited for Emlis observations.  Callers
    should use observation_status=rejected/unavailable and keep comment_text
    empty instead of filling a replacement paragraph.
    """

    return ""


__all__ = ["build_safe_understanding_fallback"]
