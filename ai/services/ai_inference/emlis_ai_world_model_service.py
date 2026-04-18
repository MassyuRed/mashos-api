# -*- coding: utf-8 -*-
from __future__ import annotations

"""World-model construction for EmlisAI."""

from typing import Any, Dict, List, Optional

from emlis_ai_types import (
    EmlisAICapabilityConfig,
    EvidenceRef,
    SourceBundle,
    WorldModel,
    WorldModelFacts,
    WorldModelHypothesis,
)


def _current_emotion_details(bundle: SourceBundle) -> List[Dict[str, Any]]:
    raw = bundle.current_input.get("emotion_details")
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    return []


def _emotion_label_from_item(item: Dict[str, Any]) -> Optional[str]:
    label = str(item.get("type") or item.get("emotion_type") or item.get("emotion") or "").strip()
    return label or None


def _extract_dominant_emotion(bundle: SourceBundle) -> tuple[Optional[str], Optional[str]]:
    details = _current_emotion_details(bundle)
    if not details:
        emotions = bundle.current_input.get("emotions")
        if isinstance(emotions, list) and emotions:
            return str(emotions[0]).strip() or None, None
        return None, None

    def _score(item: Dict[str, Any]) -> int:
        strength = str(item.get("strength") or "medium").strip().lower()
        return {"weak": 1, "medium": 2, "strong": 3}.get(strength, 2)

    top = sorted(details, key=_score, reverse=True)[0]
    return (
        _emotion_label_from_item(top),
        str(top.get("strength") or "").strip().lower() or None,
    )


def _emotion_labels(bundle: SourceBundle) -> List[str]:
    details = _current_emotion_details(bundle)
    out = [_emotion_label_from_item(item) for item in details]
    out = [v for v in out if v]
    if out:
        return out
    emotions = bundle.current_input.get("emotions")
    if isinstance(emotions, list):
        return [str(v).strip() for v in emotions if str(v).strip()]
    return []


def _current_categories(bundle: SourceBundle) -> List[str]:
    raw = bundle.current_input.get("category")
    if not isinstance(raw, list):
        return []
    return [str(v).strip() for v in raw if str(v).strip()]


def _latest_today_question_text(bundle: SourceBundle) -> Optional[str]:
    answer = bundle.latest_today_question_answer if isinstance(bundle.latest_today_question_answer, dict) else {}
    question_text = str(answer.get("question_text") or answer.get("question_text_snapshot") or "").strip()
    return question_text or None


def _latest_today_question_answer_text(bundle: SourceBundle) -> Optional[str]:
    answer = bundle.latest_today_question_answer if isinstance(bundle.latest_today_question_answer, dict) else {}
    text = str(answer.get("free_text") or answer.get("selected_choice_label") or "").strip()
    return text or None


def _build_same_day_change(bundle: SourceBundle) -> Optional[WorldModelHypothesis]:
    if not bundle.same_day_recent_inputs:
        return None

    previous = bundle.same_day_recent_inputs[0]
    prev_details = previous.get("emotion_details") if isinstance(previous.get("emotion_details"), list) else []
    prev_top = None
    prev_strength = None
    if prev_details and isinstance(prev_details[0], dict):
        prev_item = prev_details[0]
        prev_top = _emotion_label_from_item(prev_item)
        prev_strength = str(prev_item.get("strength") or "").strip().lower() or None

    current_top, current_strength = _extract_dominant_emotion(bundle)
    if not current_top or not prev_top:
        return None

    if current_top != prev_top:
        return WorldModelHypothesis(
            key="same_day_change",
            text=f"さっきの入力から、気持ちの中心が {prev_top} から {current_top} に移ってきていますね。",
            evidence=[
                EvidenceRef(kind="emotion", ref_id=str(bundle.current_input.get("id") or bundle.current_input.get("created_at") or "current"), weight=1.0),
                EvidenceRef(kind="emotion", ref_id=str(previous.get("id") or "previous"), weight=1.0),
            ],
            confidence=0.72,
        )

    if current_strength and prev_strength and current_strength != prev_strength:
        return WorldModelHypothesis(
            key="same_day_change",
            text="同じ感情でも、さっきより強さが少し動いていますね。",
            evidence=[
                EvidenceRef(kind="emotion", ref_id=str(bundle.current_input.get("id") or bundle.current_input.get("created_at") or "current"), weight=1.0),
                EvidenceRef(kind="emotion", ref_id=str(previous.get("id") or "previous"), weight=1.0),
            ],
            confidence=0.66,
        )

    return None


def _build_repeated_topic_signal(bundle: SourceBundle) -> Optional[WorldModelHypothesis]:
    if not bundle.similar_inputs:
        return None
    return WorldModelHypothesis(
        key="repeated_topic",
        text="最近の履歴の中でも、近いテーマがまた顔を出しているようです。",
        evidence=[
            EvidenceRef(kind="emotion", ref_id=str(item.get("id") or "similar"), weight=1.0)
            for item in bundle.similar_inputs[:2]
        ],
        confidence=0.64,
    )


def _build_recovery_signal(bundle: SourceBundle) -> Optional[WorldModelHypothesis]:
    summary = bundle.input_summary if isinstance(bundle.input_summary, dict) else {}
    streak_days = int(summary.get("streak_days") or 0)
    same_day_recent = bundle.same_day_recent_inputs[:1]
    current_top, current_strength = _extract_dominant_emotion(bundle)

    if streak_days <= 0 or not same_day_recent or not current_top:
        return None

    previous = same_day_recent[0]
    prev_details = previous.get("emotion_details") if isinstance(previous.get("emotion_details"), list) else []
    if not prev_details or not isinstance(prev_details[0], dict):
        return None

    prev_top = _emotion_label_from_item(prev_details[0]) or ""
    prev_strength = str(prev_details[0].get("strength") or "").strip().lower()
    if prev_top == current_top and prev_strength == current_strength:
        return None

    if current_top in {"平穏", "喜び"} and prev_top in {"不安", "悲しみ", "怒り"}:
        return WorldModelHypothesis(
            key="recovery_signal",
            text="直近の流れだけを見ると、少し落ち着く方向へ寄ってきていますね。",
            evidence=[
                EvidenceRef(kind="emotion", ref_id=str(previous.get("id") or "previous"), weight=1.0),
                EvidenceRef(kind="emotion", ref_id=str(bundle.current_input.get("id") or bundle.current_input.get("created_at") or "current"), weight=1.0),
            ],
            confidence=0.67,
        )
    return None


def build_emlis_ai_world_model(
    *,
    capability: EmlisAICapabilityConfig,
    bundle: SourceBundle,
) -> WorldModel:
    dominant_emotion, dominant_strength = _extract_dominant_emotion(bundle)
    input_summary = bundle.input_summary if isinstance(bundle.input_summary, dict) else {}
    weekly = bundle.myweb_home_summary.get("weekly") if isinstance(bundle.myweb_home_summary, dict) else {}
    weekly_top_raw = weekly.get("top") if isinstance(weekly, dict) else []
    weekly_top = [
        str(item[0]).strip()
        for item in weekly_top_raw
        if isinstance(item, list) and item and str(item[0]).strip()
    ]

    facts = WorldModelFacts(
        dominant_emotion=dominant_emotion,
        dominant_strength=dominant_strength,
        has_memo_input=bool(str(bundle.current_input.get("memo") or "").strip() or str(bundle.current_input.get("memo_action") or "").strip()),
        same_day_input_count=len(bundle.same_day_recent_inputs) + 1,
        week_input_count=int(input_summary.get("week_count") or 0),
        month_input_count=int(input_summary.get("month_count") or 0),
        streak_days=int(input_summary.get("streak_days") or 0),
        last_input_at=str(input_summary.get("last_input_at") or "").strip() or None,
        weekly_top_emotions=weekly_top,
        current_categories=_current_categories(bundle),
        current_emotion_labels=_emotion_labels(bundle),
        latest_today_question_text=_latest_today_question_text(bundle),
        latest_today_question_answer_text=_latest_today_question_answer_text(bundle),
    )

    hypotheses: List[WorldModelHypothesis] = []
    if capability.continuity_mode != "off":
        for candidate in (
            _build_same_day_change(bundle),
            _build_repeated_topic_signal(bundle),
            _build_recovery_signal(bundle),
        ):
            if candidate is not None and candidate.evidence:
                hypotheses.append(candidate)

    return WorldModel(
        facts=facts,
        hypotheses=hypotheses,
        debug={
            "history_mode": capability.history_mode,
            "same_day_recent_inputs": len(bundle.same_day_recent_inputs),
            "similar_inputs": len(bundle.similar_inputs),
        },
    )
