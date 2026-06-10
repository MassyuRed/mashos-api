# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from typing import Any

from emlis_ai_complete_sentence_planner import build_complete_sentence_plan_v2
from emlis_ai_complete_surface_realizer import build_complete_surface_realization_v2
from emlis_ai_reception_mode_resolver import (
    MODE_DAILY_UNPLEASANT,
    resolve_emlis_reception_mode_meta,
)
from emlis_ai_shared_reception_evidence import build_emlis_shared_reception_evidence_meta
from emlis_ai_state_answer_ratio_policy import build_emlis_ai_state_answer_ratio_policy
from test_emlis_ai_complete_sentence_plan_two_stage_section_meta import (
    _contains_forbidden_raw_key,
    _seed,
    _two_stage_plan,
)


def _daily_lightly_dismissed_current_input() -> dict[str, Any]:
    return {
        "id": "p4-6-daily-unpleasant-lightly-dismissed",
        "created_at": "2026-06-10T09:00:00+09:00",
        "memo": "会議で軽く流された感じが残って、帰ってからもまだ引っかかっている",
        "memo_action": "その場では黙っていたけれど、あとから距離を考えた",
        "emotion_details": [{"type": "不快", "strength": "medium"}],
        "emotions": ["不快"],
        "category": ["仕事", "人間関係"],
        "is_secret": False,
    }


def _daily_unpleasant_surface_realization() -> Any:
    sentence_plan = build_complete_sentence_plan_v2(
        sentence_plan_seed=_seed(),
        two_stage_section_surface_plan=_two_stage_plan(),
    )
    return build_complete_surface_realization_v2(sentence_plan=sentence_plan)


def test_p4_6_daily_unpleasant_material_keeps_event_and_reaction_without_low_information_overroute() -> None:
    current_input = _daily_lightly_dismissed_current_input()

    evidence = build_emlis_shared_reception_evidence_meta(current_input)
    resolver = resolve_emlis_reception_mode_meta(current_input)

    assert evidence["event_fact_present"] is True
    assert evidence["reaction_present"] is True
    assert "daily_lightly_dismissed_unpleasant_event" in evidence["event_hint_ids"]
    assert "daily_unpleasant_reception" in evidence["reception_candidate_mode_ids"]
    assert "disgust" in evidence["explicit_reaction_cue_ids"]
    assert "disgust" in evidence["explicit_emotion_label_ids"]

    assert resolver["reception_mode"] == MODE_DAILY_UNPLEASANT
    assert resolver["low_information_question_required"] is False
    assert resolver["question_required"] is False
    assert resolver["daily_unpleasant_event_reaction_anchor_ready"] is True
    assert resolver["daily_unpleasant_negative_emotion_label_present"] is True
    assert resolver["mode_selection_contract"]["daily_unpleasant_requires_event_and_reaction"] is True
    assert resolver["target_judgement_agreement_allowed"] is False
    assert resolver["action_instruction_allowed"] is False
    assert resolver["comment_text_generated"] is False
    assert resolver["public_response_key_added"] is False

    encoded = json.dumps(resolver, ensure_ascii=False, sort_keys=True)
    assert current_input["memo"] not in encoded
    assert current_input["memo_action"] not in encoded
    assert current_input["id"] not in encoded
    assert _contains_forbidden_raw_key(resolver) is False


def test_p4_6_daily_unpleasant_ratio_is_20_30_observation_and_70_80_reception() -> None:
    meta = build_emlis_ai_state_answer_ratio_policy(
        _daily_lightly_dismissed_current_input()
    ).as_meta()
    ratio = meta["resolved_ratio"]
    unit_plan = meta["ratio_basis"]["section_role_unit_plan"]
    context = meta["resolver_context"]

    assert ratio["reason"] == "daily_unpleasant_reception_light"
    assert ratio["range_key"] == "daily_reception"
    assert ratio["observation"] == 0.25
    assert ratio["human_follow"] == 0.75
    assert 0.20 <= ratio["observation"] <= 0.30
    assert 0.70 <= ratio["human_follow"] <= 0.80
    assert ratio["human_follow"] > ratio["observation"]
    assert unit_plan["observation_units"] == 1
    assert unit_plan["human_follow_units"] == 3
    assert context["p4_6_daily_unpleasant_ratio_policy_aligned"] is True
    assert context["p4_6_daily_unpleasant_observation_ratio_range"] == "20_30"
    assert context["p4_6_daily_unpleasant_reception_ratio_range"] == "70_80"
    assert context["reception_mode"] == MODE_DAILY_UNPLEASANT
    assert meta["comment_text_generated"] is False
    assert meta.get("public_response_key_added", False) is False


def test_p4_6_daily_unpleasant_surface_retains_event_reaction_and_emlis_reception_without_forbidden_shape() -> None:
    realization = _daily_unpleasant_surface_realization()

    assert realization.ready is True
    comment_text = realization.comment_text
    assert comment_text.startswith("見えたこと：\n")
    assert "\n\nEmlisから：\n" in comment_text
    assert "不快さ" in comment_text or "嫌さ" in comment_text
    assert "軽く流しにくい" in comment_text or "受け取れます" in comment_text
    assert "?" not in comment_text
    assert "？" not in comment_text
    assert "相手が悪い" not in comment_text
    assert "相手の意図" not in comment_text
    assert "構造" not in comment_text
    assert "関係性" not in comment_text
    assert "トラウマ" not in comment_text
    assert "してください" not in comment_text

    summary = realization.two_stage_surface_realization["daily_unpleasant_reception_surface_quality"]
    assert summary["p4_6_daily_unpleasant_family_tuning_applied"] is True
    assert summary["p4_6_daily_unpleasant_observation_ratio_policy_aligned"] is True
    assert summary["p4_6_daily_unpleasant_event_or_situation_anchor_retained"] is True
    assert summary["p4_6_daily_unpleasant_unpleasant_reaction_anchor_retained"] is True
    assert summary["p4_6_daily_unpleasant_emlis_reception_anchor_retained"] is True
    assert summary["p4_6_daily_unpleasant_question_only_surface_blocked"] is True
    assert summary["p4_6_daily_unpleasant_target_judgement_blocked"] is True
    assert summary["p4_6_daily_unpleasant_heavy_analysis_blocked"] is True
    assert summary["p4_6_daily_unpleasant_p6_over_insight_blocked"] is True
    assert summary["forbidden_surface_hits"] == []
    assert summary["comment_text_body_included"] is False
    assert summary["surface_text_body_included"] is False
    assert summary["raw_input_included"] is False
    assert summary["public_response_key_added"] is False
    assert summary["rn_visible_contract_changed"] is False

    meta = realization.as_meta(include_realized_text=False)
    assert _contains_forbidden_raw_key(meta) is False
    assert meta["comment_text_body_included"] is False
    assert meta.get("public_response_key_added", False) is False
