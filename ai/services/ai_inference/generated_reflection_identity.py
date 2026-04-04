# -*- coding: utf-8 -*-
"""Helpers for Premium generated Reflection public identity.

Public/generated Reflections are exposed as question cards.
The stable public identity is the generated q_key derived from the public
question text, not the internal topic_key.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

_WS_RE = re.compile(r"\s+")
_QKEY_PUNCT_RE = re.compile(r"[。．.!！?？、,「」『』【】\[\]（）()<>＜＞\"'`]+")



def collapse_generated_question_text(question: Any) -> str:
    text = str(question or "")
    text = _WS_RE.sub(" ", text).strip().lower()
    return text



def normalize_generated_question_text_for_key(question: Any) -> str:
    text = collapse_generated_question_text(question)
    text = _QKEY_PUNCT_RE.sub("", text)
    text = _WS_RE.sub("", text)
    return text



def compute_generated_question_q_key(question: Any) -> str:
    normalized = normalize_generated_question_text_for_key(question)
    if not normalized:
        return "generated:q:unknown"
    return f"generated:q:{hashlib.md5(normalized.encode('utf-8')).hexdigest()}"


__all__ = [
    "collapse_generated_question_text",
    "compute_generated_question_q_key",
    "normalize_generated_question_text_for_key",
]
