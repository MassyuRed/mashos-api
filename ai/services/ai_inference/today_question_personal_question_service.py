# -*- coding: utf-8 -*-
from __future__ import annotations

"""Build display-ready personal Today Question payloads from candidates."""

from typing import Any, Dict, Mapping, Optional

from today_question_personal_templates import (
    QUESTION_ORIGIN_PERSONAL,
    build_question_text,
    build_source_anchor_payload,
    choices_snapshot_for_type,
    normalize_question_type,
)


def build_personal_question_insert_payload(
    *,
    user_id: str,
    candidate_id: str,
    candidate: Mapping[str, Any],
    service_day_key: str,
) -> Optional[Dict[str, Any]]:
    qtype = normalize_question_type(candidate.get("question_type"))
    anchor = str(candidate.get("anchor_text") or "").strip()
    uid = str(user_id or "").strip()
    cid = str(candidate_id or "").strip()
    day = str(service_day_key or "").strip()
    if not uid or not cid or not day or not qtype or not anchor:
        return None
    choices = choices_snapshot_for_type(qtype)
    if not choices:
        return None
    question_text = build_question_text(anchor_text=anchor, question_type=qtype)
    if not question_text:
        return None
    source_anchor = build_source_anchor_payload(candidate)
    return {
        "user_id": uid,
        "candidate_id": cid,
        "question_text": question_text,
        "question_type": qtype,
        "choices_snapshot_json": choices,
        "source_anchor_json": source_anchor,
        "status": "ready",
        "presented_local_date": day,
        "question_origin": QUESTION_ORIGIN_PERSONAL,
    }
