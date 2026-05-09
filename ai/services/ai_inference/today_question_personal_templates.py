# -*- coding: utf-8 -*-
from __future__ import annotations

"""Deterministic templates for personal Today Question follow-ups.

This module intentionally contains no DB access and no generative model calls.
It keeps the user-visible question text and fixed choice sets stable so that
personal follow-up questions remain source-grounded and snapshot-safe.
"""

import hashlib
from typing import Any, Dict, List, Mapping, Optional

QUESTION_ORIGIN_STATIC = "static_role_probe"
QUESTION_ORIGIN_PERSONAL = "personal_followup"

# MVP question types from the vNext design.
QUESTION_TYPE_REASON_FOR_OBLIGATION = "reason_for_obligation"
QUESTION_TYPE_JOY_OR_VALUE = "joy_or_value"
QUESTION_TYPE_WISH_BEHIND_DISCOMFORT = "wish_behind_discomfort"
QUESTION_TYPE_PROTECTED_VALUE = "protected_value"
QUESTION_TYPE_AFTER_ACTION_CHANGE = "after_action_change"
QUESTION_TYPE_RELATIONSHIP_MEANING = "relationship_meaning"

PERSONAL_TODAY_QUESTION_TYPES = {
    QUESTION_TYPE_REASON_FOR_OBLIGATION,
    QUESTION_TYPE_JOY_OR_VALUE,
    QUESTION_TYPE_WISH_BEHIND_DISCOMFORT,
    QUESTION_TYPE_PROTECTED_VALUE,
    QUESTION_TYPE_AFTER_ACTION_CHANGE,
    QUESTION_TYPE_RELATIONSHIP_MEANING,
}

QUESTION_TEMPLATES: Dict[str, str] = {
    QUESTION_TYPE_REASON_FOR_OBLIGATION: "そのとき、なぜ{anchor_core}と感じていましたか？",
    QUESTION_TYPE_JOY_OR_VALUE: "{anchor_core}ことで、どんな嬉しさを感じていますか？",
    QUESTION_TYPE_WISH_BEHIND_DISCOMFORT: "本当は、どうなってほしかったですか？",
    QUESTION_TYPE_PROTECTED_VALUE: "そのとき、何を守りたかったのに近いですか？",
    QUESTION_TYPE_AFTER_ACTION_CHANGE: "そのあと、気持ちはどのように変わりましたか？",
    QUESTION_TYPE_RELATIONSHIP_MEANING: "その関わりの中で、何を大切にしたかったですか？",
}

_FIXED_CHOICES: Dict[str, List[Dict[str, Any]]] = {
    QUESTION_TYPE_REASON_FOR_OBLIGATION: [
        {
            "choice_key": "meet_expectations",
            "label": "期待に応えたいから",
            "hidden_meta": {
                "analysis_tags": ["responsibility", "expectation", "effort_pressure"],
                "world_kind_hint": "self",
                "target_hint": "relationship",
                "role_hint": "supporter_or_achiever",
            },
        },
        {
            "choice_key": "avoid_burden",
            "label": "迷惑をかけたくないから",
            "hidden_meta": {
                "analysis_tags": ["responsibility", "avoid_burden", "relationship_sensitivity"],
                "world_kind_hint": "self",
                "target_hint": "relationship",
                "role_hint": "defender_or_supporter",
            },
        },
        {
            "choice_key": "avoid_delay",
            "label": "遅れたくないから",
            "hidden_meta": {
                "analysis_tags": ["pace", "comparison", "achievement_pressure"],
                "world_kind_hint": "self",
                "target_hint": "activity",
                "role_hint": "achiever",
            },
        },
        {
            "choice_key": "self_consent",
            "label": "自分で納得したいから",
            "hidden_meta": {
                "analysis_tags": ["self_consent", "standards", "agency"],
                "world_kind_hint": "self",
                "target_hint": "self",
                "role_hint": "seeker",
            },
        },
        {
            "choice_key": "not_sure",
            "label": "まだ分からない",
            "hidden_meta": {
                "analysis_tags": ["unclear_reason"],
                "world_kind_hint": "self",
                "target_hint": "self",
                "role_hint": "observer",
            },
        },
    ],
    QUESTION_TYPE_JOY_OR_VALUE: [
        {
            "choice_key": "share_together",
            "label": "分かち合えること",
            "hidden_meta": {
                "analysis_tags": ["sharing", "connection", "joy"],
                "world_kind_hint": "relationship",
                "target_hint": "relationship",
                "role_hint": "connector",
            },
        },
        {
            "choice_key": "being_received",
            "label": "受け取ってもらえること",
            "hidden_meta": {
                "analysis_tags": ["acceptance", "expression", "relief"],
                "world_kind_hint": "relationship",
                "target_hint": "relationship",
                "role_hint": "communicator",
            },
        },
        {
            "choice_key": "knowing_others",
            "label": "相手を知れること",
            "hidden_meta": {
                "analysis_tags": ["curiosity", "relationship", "understanding_others"],
                "world_kind_hint": "relationship",
                "target_hint": "person",
                "role_hint": "observer",
            },
        },
        {
            "choice_key": "expanding_thoughts",
            "label": "考えが広がること",
            "hidden_meta": {
                "analysis_tags": ["learning", "perspective", "growth"],
                "world_kind_hint": "outside",
                "target_hint": "concept",
                "role_hint": "seeker",
            },
        },
        {
            "choice_key": "being_helpful",
            "label": "役に立てること",
            "hidden_meta": {
                "analysis_tags": ["contribution", "usefulness", "care"],
                "world_kind_hint": "relationship",
                "target_hint": "relationship",
                "role_hint": "supporter",
            },
        },
        {
            "choice_key": "not_sure",
            "label": "まだ分からない",
            "hidden_meta": {
                "analysis_tags": ["unclear_value"],
                "world_kind_hint": "self",
                "target_hint": "self",
                "role_hint": "observer",
            },
        },
    ],
    QUESTION_TYPE_WISH_BEHIND_DISCOMFORT: [
        {
            "choice_key": "wanted_understanding",
            "label": "分かってほしかった",
            "hidden_meta": {
                "analysis_tags": ["wish", "understanding", "relationship"],
                "world_kind_hint": "relationship",
                "target_hint": "relationship",
                "role_hint": "communicator",
            },
        },
        {
            "choice_key": "wanted_safety",
            "label": "安心したかった",
            "hidden_meta": {
                "analysis_tags": ["wish", "safety", "relief"],
                "world_kind_hint": "self",
                "target_hint": "environment",
                "role_hint": "defender",
            },
        },
        {
            "choice_key": "wanted_respect",
            "label": "尊重されたかった",
            "hidden_meta": {
                "analysis_tags": ["wish", "respect", "boundary"],
                "world_kind_hint": "relationship",
                "target_hint": "relationship",
                "role_hint": "defender",
            },
        },
        {
            "choice_key": "wanted_together",
            "label": "一緒に考えたかった",
            "hidden_meta": {
                "analysis_tags": ["wish", "cooperation", "dialogue"],
                "world_kind_hint": "relationship",
                "target_hint": "relationship",
                "role_hint": "connector",
            },
        },
        {
            "choice_key": "not_sure",
            "label": "まだ分からない",
            "hidden_meta": {
                "analysis_tags": ["unclear_wish"],
                "world_kind_hint": "self",
                "target_hint": "self",
                "role_hint": "observer",
            },
        },
    ],
    QUESTION_TYPE_PROTECTED_VALUE: [
        {
            "choice_key": "my_pace",
            "label": "自分のペース",
            "hidden_meta": {
                "analysis_tags": ["protected_value", "pace", "boundary"],
                "world_kind_hint": "self",
                "target_hint": "self",
                "role_hint": "defender",
            },
        },
        {
            "choice_key": "safe_relationship",
            "label": "安心できる関係",
            "hidden_meta": {
                "analysis_tags": ["protected_value", "safe_relationship", "trust"],
                "world_kind_hint": "relationship",
                "target_hint": "relationship",
                "role_hint": "defender_or_connector",
            },
        },
        {
            "choice_key": "convincing_reason",
            "label": "納得できる理由",
            "hidden_meta": {
                "analysis_tags": ["protected_value", "reason", "understanding"],
                "world_kind_hint": "self",
                "target_hint": "concept",
                "role_hint": "seeker",
            },
        },
        {
            "choice_key": "avoid_more_exhaustion",
            "label": "これ以上疲れないこと",
            "hidden_meta": {
                "analysis_tags": ["protected_value", "fatigue", "limit"],
                "world_kind_hint": "self",
                "target_hint": "self",
                "role_hint": "defender",
            },
        },
        {
            "choice_key": "not_sure",
            "label": "まだ分からない",
            "hidden_meta": {
                "analysis_tags": ["unclear_protected_value"],
                "world_kind_hint": "self",
                "target_hint": "self",
                "role_hint": "observer",
            },
        },
    ],
    QUESTION_TYPE_AFTER_ACTION_CHANGE: [
        {
            "choice_key": "calmed_down",
            "label": "落ち着いた",
            "hidden_meta": {
                "analysis_tags": ["after_action", "calm", "recovery"],
                "world_kind_hint": "self",
                "target_hint": "activity",
                "role_hint": "regulator",
            },
        },
        {
            "choice_key": "space_returned",
            "label": "余裕が戻った",
            "hidden_meta": {
                "analysis_tags": ["after_action", "space", "recovery"],
                "world_kind_hint": "self",
                "target_hint": "self",
                "role_hint": "regulator",
            },
        },
        {
            "choice_key": "still_tired",
            "label": "まだ疲れていた",
            "hidden_meta": {
                "analysis_tags": ["after_action", "fatigue", "remaining_load"],
                "world_kind_hint": "self",
                "target_hint": "self",
                "role_hint": "observer",
            },
        },
        {
            "choice_key": "organized",
            "label": "気持ちが整理された",
            "hidden_meta": {
                "analysis_tags": ["after_action", "clarity", "reflection"],
                "world_kind_hint": "self",
                "target_hint": "concept",
                "role_hint": "seeker",
            },
        },
        {
            "choice_key": "not_sure",
            "label": "まだ分からない",
            "hidden_meta": {
                "analysis_tags": ["unclear_after_action"],
                "world_kind_hint": "self",
                "target_hint": "self",
                "role_hint": "observer",
            },
        },
    ],
    QUESTION_TYPE_RELATIONSHIP_MEANING: [
        {
            "choice_key": "mutual_understanding",
            "label": "分かり合うこと",
            "hidden_meta": {
                "analysis_tags": ["relationship", "mutual_understanding", "connection"],
                "world_kind_hint": "relationship",
                "target_hint": "relationship",
                "role_hint": "connector",
            },
        },
        {
            "choice_key": "distance",
            "label": "距離感",
            "hidden_meta": {
                "analysis_tags": ["relationship", "distance", "boundary"],
                "world_kind_hint": "relationship",
                "target_hint": "relationship",
                "role_hint": "defender",
            },
        },
        {
            "choice_key": "being_helpful",
            "label": "役に立つこと",
            "hidden_meta": {
                "analysis_tags": ["relationship", "contribution", "support"],
                "world_kind_hint": "relationship",
                "target_hint": "relationship",
                "role_hint": "supporter",
            },
        },
        {
            "choice_key": "being_myself",
            "label": "自分らしさ",
            "hidden_meta": {
                "analysis_tags": ["relationship", "self_expression", "authenticity"],
                "world_kind_hint": "self",
                "target_hint": "self",
                "role_hint": "communicator",
            },
        },
        {
            "choice_key": "not_sure",
            "label": "まだ分からない",
            "hidden_meta": {
                "analysis_tags": ["unclear_relationship_value"],
                "world_kind_hint": "relationship",
                "target_hint": "relationship",
                "role_hint": "observer",
            },
        },
    ],
}


def normalize_question_type(raw: Any) -> Optional[str]:
    value = str(raw or "").strip()
    if value in PERSONAL_TODAY_QUESTION_TYPES:
        return value
    return None


def build_source_hash(*, source_id: Any, source_field: Any, anchor_text: Any, question_type: Any) -> str:
    raw = "|".join(
        [
            str(source_id or "").strip(),
            str(source_field or "").strip(),
            str(anchor_text or "").strip(),
            str(question_type or "").strip(),
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def choices_snapshot_for_type(question_type: str) -> List[Dict[str, Any]]:
    qtype = normalize_question_type(question_type)
    if not qtype:
        return []
    out: List[Dict[str, Any]] = []
    for idx, choice in enumerate(_FIXED_CHOICES.get(qtype, []), start=1):
        choice_key = str(choice.get("choice_key") or "").strip()
        if not choice_key:
            continue
        out.append(
            {
                "choice_id": choice_key,
                "choice_key": choice_key,
                "label": str(choice.get("label") or "").strip(),
                "sort_order": idx,
                "hidden_meta": dict(choice.get("hidden_meta") or {}),
            }
        )
    return out


def build_question_text(*, anchor_text: str, question_type: str) -> str:
    qtype = normalize_question_type(question_type)
    anchor = str(anchor_text or "").strip()
    if not qtype or not anchor:
        return ""
    template = QUESTION_TEMPLATES.get(qtype) or "この入力について、もう少しだけ教えてください。"
    body = template.format(anchor_core=anchor)
    return f"「{anchor}」と残していました。\n{body}"


def build_source_anchor_payload(candidate: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "source_type": str(candidate.get("source_type") or "emotion_input").strip() or "emotion_input",
        "source_id": str(candidate.get("source_id") or "").strip(),
        "source_field": str(candidate.get("source_field") or "").strip(),
        "anchor_text": str(candidate.get("anchor_text") or "").strip(),
        "anchor_start": candidate.get("anchor_start"),
        "anchor_end": candidate.get("anchor_end"),
        "question_type": str(candidate.get("question_type") or "").strip(),
        "source_hash": str(candidate.get("source_hash") or "").strip(),
    }


def source_anchor_hash(source_anchor: Mapping[str, Any]) -> str:
    return build_source_hash(
        source_id=source_anchor.get("source_id"),
        source_field=source_anchor.get("source_field"),
        anchor_text=source_anchor.get("anchor_text"),
        question_type=source_anchor.get("question_type"),
    )
