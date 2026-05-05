# -*- coding: utf-8 -*-
from __future__ import annotations

"""World-model construction for EmlisAI.

This module builds raw facts and lightweight hypothesis candidates. Final
interpretation arbitration is handled later by the observation kernel.
"""

from typing import Any, Dict, List, Optional

from emlis_ai_types import (
    EmlisAICapabilityConfig,
    EmotionDisplayItem,
    EvidenceRef,
    SourceBundle,
    UserWordAnchor,
    WorldModel,
    WorldModelFacts,
    WorldModelHypothesis,
)
from emlis_ai_user_word_anchor_service import extract_user_word_anchors
from emlis_ai_phrase_shaping_service import shape_user_phrases
from emlis_ai_understanding_frame_service import build_understanding_frame
from emlis_ai_input_meaning_block_service import (
    build_input_meaning_blocks,
    build_meaning_coverage_plan,
    build_major_meaning_retention_plan,
    build_whole_input_meaning_arc,
)
from emlis_ai_response_composition_service import (
    build_response_composition_plan,
    build_reply_narrative_arc,
)


def _current_emotion_details(bundle: SourceBundle) -> List[Dict[str, Any]]:
    raw = bundle.current_input.get("emotion_details")
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    return []


def _emotion_label_from_item(item: Dict[str, Any]) -> Optional[str]:
    label = str(item.get("type") or item.get("emotion_type") or item.get("emotion") or "").strip()
    return label or None


def _strength_score(strength: Any) -> int:
    return {"weak": 1, "medium": 2, "strong": 3}.get(str(strength or "").strip().lower(), 2)


def _strength_label(strength: Any) -> str:
    return {"weak": "弱", "medium": "中", "strong": "強"}.get(str(strength or "").strip().lower(), "")


def _selected_emotion_items(bundle: SourceBundle) -> List[EmotionDisplayItem]:
    details = _current_emotion_details(bundle)
    if details:
        indexed: List[tuple[int, Dict[str, Any]]] = list(enumerate(details))
        top_index = sorted(indexed, key=lambda pair: (_strength_score(pair[1].get("strength")), -pair[0]), reverse=True)[0][0]
        out: List[EmotionDisplayItem] = []
        for idx, item in indexed:
            label = _emotion_label_from_item(item)
            if not label:
                continue
            strength = str(item.get("strength") or "").strip().lower()
            out.append(
                EmotionDisplayItem(
                    type=label,
                    strength=strength,
                    strength_label=_strength_label(strength),
                    role="dominant" if idx == top_index else "secondary",
                )
            )
        return out

    emotions = bundle.current_input.get("emotions")
    if not isinstance(emotions, list):
        return []
    out = []
    for idx, value in enumerate(emotions):
        label = str(value or "").strip()
        if not label:
            continue
        out.append(EmotionDisplayItem(type=label, role="dominant" if idx == 0 else "secondary"))
    return out


def _anchor_limit_for_capability(capability: EmlisAICapabilityConfig) -> int:
    # Complex self-awareness inputs need enough current-input anchors even on Free;
    # plan difference is in history/model scope, not in whether the current input is understood.
    if capability.tier == "premium":
        return 12
    if capability.tier == "plus":
        return 10
    return 8


def _memo_richness(bundle: SourceBundle) -> str:
    char_count = len(str(bundle.current_input.get("memo") or "").strip()) + len(str(bundle.current_input.get("memo_action") or "").strip())
    if char_count <= 0:
        return "none"
    if char_count < 50:
        return "short"
    if char_count < 140:
        return "medium"
    return "long"


def _response_mode(*, labels: List[str], categories: List[str], anchors: List[UserWordAnchor], memo_richness: str) -> str:
    label_set = set(labels)
    category_text = " ".join(categories)
    anchor_text = " ".join(anchor.text for anchor in anchors)
    combined = f"{category_text} {anchor_text}"
    if "喜び" in label_set:
        return "celebrate"
    if "怒り" in label_set:
        return "protect_boundary"
    if "平穏" in label_set and memo_richness in {"none", "short"}:
        return "quiet_receive"
    if any(v in label_set for v in {"悲しみ", "不安", "恐れ", "焦り"}):
        if any(word in combined for word in ("恋人", "相手", "家族", "友達", "すれ違", "わかり合", "分かり合")):
            return "comfort"
        return "organize" if memo_richness in {"medium", "long"} else "comfort"
    if any(word in combined for word in ("整理", "考え", "価値観", "仕事", "学習")):
        return "organize"
    return "receive"


def _extract_dominant_emotion(bundle: SourceBundle) -> tuple[Optional[str], Optional[str]]:
    details = _current_emotion_details(bundle)
    if not details:
        emotions = bundle.current_input.get("emotions")
        if isinstance(emotions, list) and emotions:
            return str(emotions[0]).strip() or None, None
        return None, None

    top = sorted(details, key=lambda item: _strength_score(item.get("strength")), reverse=True)[0]
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


def _current_ref(bundle: SourceBundle) -> EvidenceRef:
    return EvidenceRef(
        kind="emotion",
        ref_id=str(bundle.current_input.get("id") or bundle.current_input.get("created_at") or "current"),
        weight=1.0,
    )


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
            evidence=[_current_ref(bundle), EvidenceRef(kind="emotion", ref_id=str(previous.get("id") or "previous"), weight=1.0)],
            confidence=0.72,
        )

    if current_strength and prev_strength and current_strength != prev_strength:
        return WorldModelHypothesis(
            key="same_day_change",
            text="同じ感情でも、さっきから感じ方が少し動いていますね。",
            evidence=[_current_ref(bundle), EvidenceRef(kind="emotion", ref_id=str(previous.get("id") or "previous"), weight=1.0)],
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
                _current_ref(bundle),
            ],
            confidence=0.67,
        )
    return None


def _collect_unknowns(bundle: SourceBundle, facts: WorldModelFacts) -> List[str]:
    unknowns: List[str] = []
    if not facts.current_emotion_labels:
        unknowns.append("current_emotion_labels_missing")
    if not facts.current_categories:
        unknowns.append("current_categories_sparse")
    if not bundle.same_day_recent_inputs and not bundle.similar_inputs:
        unknowns.append("history_signal_sparse")
    return unknowns


def _collect_conflicts(hypotheses: List[WorldModelHypothesis]) -> List[str]:
    keys = {item.key for item in hypotheses}
    conflicts: List[str] = []
    if "same_day_change" in keys and "recovery_signal" in keys:
        conflicts.append("same_day_change_and_recovery_both_present")
    return conflicts


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

    selected_emotions = _selected_emotion_items(bundle)
    secondary_emotions = [item for item in selected_emotions if item.role != "dominant"]
    current_ref = _current_ref(bundle)
    user_word_anchors = extract_user_word_anchors(
        current_input=bundle.current_input,
        max_anchors=_anchor_limit_for_capability(capability),
        evidence=current_ref,
    )
    shaped_user_phrases = shape_user_phrases(
        anchors=user_word_anchors,
        current_input=bundle.current_input,
    )
    meaning_blocks = build_input_meaning_blocks(
        current_input=bundle.current_input,
        shaped_user_phrases=shaped_user_phrases,
        evidence=current_ref,
    )
    meaning_coverage_plan = build_meaning_coverage_plan(
        current_input=bundle.current_input,
        meaning_blocks=meaning_blocks,
    )
    whole_input_meaning_arc = build_whole_input_meaning_arc(
        meaning_blocks=meaning_blocks,
        evidence=current_ref,
    )
    major_meaning_retention_plan = build_major_meaning_retention_plan(
        meaning_blocks=meaning_blocks,
        coverage_plan=meaning_coverage_plan,
        whole_input_meaning_arc=whole_input_meaning_arc,
    )
    response_composition_plan = build_response_composition_plan(
        input_level=meaning_coverage_plan.input_level,
        clear_long_input=bool(meaning_coverage_plan.clear_long_input),
        meaning_blocks=meaning_blocks,
    )
    reply_narrative_arc = build_reply_narrative_arc(
        composition_plan=response_composition_plan,
        meaning_blocks=meaning_blocks,
    )
    current_categories = _current_categories(bundle)
    current_emotion_labels = _emotion_labels(bundle)
    memo_richness = _memo_richness(bundle)
    response_mode = _response_mode(
        labels=current_emotion_labels,
        categories=current_categories,
        anchors=user_word_anchors,
        memo_richness=memo_richness,
    )
    understanding_frame = build_understanding_frame(
        anchors=user_word_anchors,
        selected_emotions=selected_emotions,
        current_input=bundle.current_input,
        evidence=current_ref,
    )
    understanding_patterns = list(getattr(understanding_frame, "relation_patterns", []) or [])

    facts = WorldModelFacts(
        dominant_emotion=dominant_emotion,
        dominant_strength=dominant_strength,
        has_memo_input=bool(str(bundle.current_input.get("memo") or "").strip() or str(bundle.current_input.get("memo_action") or "").strip()),
        selected_emotions=selected_emotions,
        secondary_emotions=secondary_emotions,
        user_word_anchors=user_word_anchors,
        shaped_user_phrases=shaped_user_phrases,
        response_mode=response_mode,
        memo_richness=memo_richness,
        understanding_frame=understanding_frame,
        understanding_patterns=understanding_patterns,
        meaning_blocks=meaning_blocks,
        meaning_coverage_plan=meaning_coverage_plan,
        whole_input_meaning_arc=whole_input_meaning_arc,
        major_meaning_retention_plan=major_meaning_retention_plan,
        response_composition_plan=response_composition_plan,
        reply_narrative_arc=reply_narrative_arc,
        same_day_input_count=len(bundle.same_day_recent_inputs) + 1,
        week_input_count=int(input_summary.get("week_count") or 0),
        month_input_count=int(input_summary.get("month_count") or 0),
        streak_days=int(input_summary.get("streak_days") or 0),
        last_input_at=str(input_summary.get("last_input_at") or "").strip() or None,
        weekly_top_emotions=weekly_top,
        current_categories=current_categories,
        current_emotion_labels=current_emotion_labels,
        latest_today_question_text=_latest_today_question_text(bundle),
        latest_today_question_answer_text=_latest_today_question_answer_text(bundle),
    )

    hypotheses: List[WorldModelHypothesis] = []
    rejected_hypotheses: List[WorldModelHypothesis] = []
    if capability.continuity_mode != "off":
        for candidate in (
            _build_same_day_change(bundle),
            _build_repeated_topic_signal(bundle),
            _build_recovery_signal(bundle),
        ):
            if candidate is None:
                continue
            if candidate.evidence:
                hypotheses.append(candidate)
            else:
                rejected_hypotheses.append(candidate)

    unknowns = _collect_unknowns(bundle, facts)
    conflicts = _collect_conflicts(hypotheses)
    if bundle.derived_user_model is not None and not bundle.derived_user_model.interpretive_frame.meaning_map:
        unknowns.append("derived_model_meaning_map_sparse")

    return WorldModel(
        facts=facts,
        hypotheses=hypotheses,
        unknowns=unknowns,
        conflicts=conflicts,
        rejected_hypotheses=rejected_hypotheses,
        debug={
            "history_mode": capability.history_mode,
            "same_day_recent_inputs": len(bundle.same_day_recent_inputs),
            "similar_inputs": len(bundle.similar_inputs),
            "derived_model_loaded": bool(bundle.derived_user_model is not None),
            "user_word_anchor_count": len(user_word_anchors),
            "shaped_user_phrase_count": len(shaped_user_phrases),
            "unsafe_phrase_count": sum(1 for item in shaped_user_phrases if getattr(item, "usability", "safe") == "unsafe"),
            "understanding_patterns": understanding_patterns,
            "understanding_frame_confidence": float(getattr(understanding_frame, "confidence", 0.0) or 0.0),
            "meaning_block_count": len(meaning_blocks),
            "meaning_coverage_input_level": meaning_coverage_plan.input_level,
            "meaning_coverage_clear_long_input": bool(meaning_coverage_plan.clear_long_input),
            "meaning_coverage_selected_block_keys": list(meaning_coverage_plan.selected_block_keys),
            "whole_input_meaning_arc_key": str(getattr(whole_input_meaning_arc, "arc_key", "") or ""),
            "major_meaning_must_keep_block_keys": list(getattr(major_meaning_retention_plan, "must_keep_block_keys", []) or []),
            "response_composition_key": str(getattr(response_composition_plan, "composition_key", "") or ""),
            "reply_narrative_arc_key": str(getattr(reply_narrative_arc, "arc_key", "") or ""),
            "response_mode": response_mode,
            "memo_richness": memo_richness,
        },
    )
