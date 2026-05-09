# -*- coding: utf-8 -*-
from __future__ import annotations

"""Retired legacy input-feedback text templates.

EmlisAI observations are now generated through the multi-perspective pipeline
and fail closed.  This compatibility shim intentionally contains no observation
sentence templates and returns an empty string when called by older code.
"""

from typing import Any


def build_input_feedback_comment(*_: Any, **__: Any) -> str:
    """Do not generate a legacy fixed Emlis observation."""

    return ""


__all__ = ["build_input_feedback_comment"]
