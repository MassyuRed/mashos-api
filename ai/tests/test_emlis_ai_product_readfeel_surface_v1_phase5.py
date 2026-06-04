# -*- coding: utf-8 -*-
from __future__ import annotations

from emlis_ai_complete_composer_types import CompleteSentencePlanLine, CompleteSentencePlanV2
from emlis_ai_complete_surface_realizer import build_complete_surface_realization_v2
from emlis_ai_state_answer_ratio_policy import build_emlis_ai_state_answer_ratio_policy
from emlis_ai_two_stage_section_surface_plan import build_two_stage_section_surface_plan


def _two_stage_line(
    *,
    sentence_id: str,
    roles: tuple[str, ...],
    section_id: str,
    order_index: int,
    mode_id: str,
    line_role: str = "opening",
    relation_type: str = "center",
) -> CompleteSentencePlanLine:
    label = "見えたこと" if section_id == "observation" else "Emlisから"
    return CompleteSentencePlanLine(
        sentence_id=sentence_id,
        line_role=line_role,
        relation_type=relation_type,
        phrase_unit_ids=(f"pu_{sentence_id}",),
        evidence_span_ids=(f"span_{sentence_id}",),
        must_include_roles=roles,
        meta={
            "two_stage_section_id": section_id,
            "two_stage_section_role": "state_answer_observation" if section_id == "observation" else "human_reception",
            "two_stage_display_label": label,
            "two_stage_comment_text_section_label": f"{label}：",
            "two_stage_section_label_required": True,
            "two_stage_section_order_index": order_index,
            "two_stage_expected_comment_text_shape": "labelled_two_stage_text",
            "two_stage_section_surface_plan_required": True,
            "two_stage_reception_mode_id": mode_id,
        },
    )


def _two_stage_plan(mode_id: str, lines: tuple[CompleteSentencePlanLine, ...]) -> CompleteSentencePlanV2:
    return CompleteSentencePlanV2(
        plan_id=f"phase5_product_readfeel_v1_{mode_id}",
        coverage_group="phase5_product_readfeel_v1_surface",
        sentence_budget=len(lines),
        sentence_plans=lines,
        meta={
            "two_stage_section_surface_plan_required": True,
            "two_stage_expected_comment_text_shape": "labelled_two_stage_text",
            "two_stage_section_labels_required": True,
        },
    )


def test_phase5_daily_positive_surface_keeps_positive_temperature_without_overweighting() -> None:
    realization = build_complete_surface_realization_v2(
        sentence_plan=_two_stage_plan(
            "daily_positive_reception",
            (
                _two_stage_line(
                    sentence_id="phase5_positive_obs",
                    roles=("work_fatigue", "conversation_wish"),
                    section_id="observation",
                    order_index=0,
                    mode_id="daily_positive_reception",
                ),
                _two_stage_line(
                    sentence_id="phase5_positive_rec",
                    roles=("achievement", "joy_or_surprise"),
                    section_id="reception",
                    order_index=1,
                    mode_id="daily_positive_reception",
                    line_role="relation",
                    relation_type="recovery",
                ),
            ),
        )
    )

    assert realization.status == "ready"
    assert "見えたこと：" in realization.comment_text
    assert "Emlisから：" in realization.comment_text
    assert "誰かと話したい気持ち" in realization.comment_text
    assert "嬉しさ" in realization.comment_text
    assert "強く動いた変化" in realization.comment_text
    assert "負荷と" not in realization.comment_text
    assert "前の疲れ" not in realization.comment_text
    assert "完全に回復" not in realization.comment_text
    assert "もっと" not in realization.comment_text

    summary = realization.two_stage_surface_realization["mode_specific_two_stage_surface_policy"]
    assert "daily_positive_reception" in summary["mode_ids"]
    assert "positive_surface_not_overweighted" in summary["feature_families"]
    meta = realization.as_meta(include_realized_text=False)
    assert meta["public_response_key_change"] is False
    assert meta.get("rn_visible_contract_changed") is not True
    assert meta["raw_input_included"] is False
    assert meta["comment_text_body_included"] is False


def test_phase5_daily_positive_positive_only_does_not_invent_work_fatigue_or_burden() -> None:
    realization = build_complete_surface_realization_v2(
        sentence_plan=_two_stage_plan(
            "daily_positive_reception",
            (
                _two_stage_line(
                    sentence_id="phase5_positive_only_obs",
                    roles=("achievement", "positive_change"),
                    section_id="observation",
                    order_index=0,
                    mode_id="daily_positive_reception",
                ),
                _two_stage_line(
                    sentence_id="phase5_positive_only_rec",
                    roles=("positive_change", "joy_or_surprise"),
                    section_id="reception",
                    order_index=1,
                    mode_id="daily_positive_reception",
                    line_role="relation",
                    relation_type="recovery",
                ),
                _two_stage_line(
                    sentence_id="phase5_positive_only_close",
                    roles=("joy_or_surprise",),
                    section_id="reception",
                    order_index=2,
                    mode_id="daily_positive_reception",
                    line_role="closing",
                    relation_type="center",
                ),
            ),
        )
    )

    assert realization.status == "ready"
    assert "嬉しさ" in realization.comment_text
    assert "小さく動いた" in realization.comment_text
    assert "仕事後" not in realization.comment_text
    assert "疲れ" not in realization.comment_text
    assert "負荷" not in realization.comment_text
    assert "前の疲れ" not in realization.comment_text
    assert "回復" not in realization.comment_text

    summary = realization.two_stage_surface_realization["product_readfeel_v1_surface_policy"]
    assert summary["families"] == ["daily_positive"]
    assert summary["positive_surface_not_overweighted"] is True
    assert summary["red_or_repair_surface_blocker_count"] == 0
    assert summary["comment_text_body_included"] is False
    assert summary["raw_input_included"] is False


def test_phase5_self_denial_surface_keeps_identity_claim_separate_from_felt_state() -> None:
    realization = build_complete_surface_realization_v2(
        sentence_plan=_two_stage_plan(
            "self_denial_support",
            (
                _two_stage_line(
                    sentence_id="phase5_self_denial_obs",
                    roles=("self_denial", "attempt_to_change"),
                    section_id="observation",
                    order_index=0,
                    mode_id="self_denial_support",
                ),
                _two_stage_line(
                    sentence_id="phase5_self_denial_rec",
                    roles=("self_denial", "challenge_attempt"),
                    section_id="reception",
                    order_index=1,
                    mode_id="self_denial_support",
                    line_role="relation",
                    relation_type="contrast",
                ),
            ),
        )
    )

    assert realization.status == "ready"
    assert "本人の事実" in realization.comment_text
    assert "直したい気持ち" in realization.comment_text or "挑戦しようとする動き" in realization.comment_text
    assert "中途半端な人" not in realization.comment_text
    assert "自信を持ちましょう" not in realization.comment_text
    assert "あなたは本当はすごい人" not in realization.comment_text
    assert "診断" not in realization.comment_text

    summary = realization.two_stage_surface_realization["mode_specific_two_stage_surface_policy"]
    assert "self_denial_support" in summary["mode_ids"]
    assert "felt_state_identity_claim_separated" in summary["feature_families"]
    meta = realization.as_meta(include_realized_text=False)
    assert meta["public_response_key_change"] is False
    assert meta["raw_input_included"] is False


def test_phase5_ratio_only_section_plan_maps_v1_surface_modes_without_case_branch() -> None:
    plan = build_two_stage_section_surface_plan(
        {
            "two_stage_display_required": True,
            "resolved_ratio": {"reason": "daily_positive_reception_light"},
            "sections": [
                {"section_id": "observation", "section_role": "state_answer_observation"},
                {"section_id": "reception", "section_role": "human_follow"},
            ],
        }
    )

    assert plan["reception_mode_id"] == "daily_positive_reception"
    assert plan["reception_mode_source"] == "role_or_surface.resolved_ratio.reason"
    assert plan["mode_section_budget"] == {
        "observation_min": 1,
        "observation_max": 1,
        "reception_min": 2,
        "reception_max": 2,
    }
    observation, reception = plan["sections"]
    assert "positive_change_seen_without_heavy_analysis" in observation["allowed_surface_intents"]
    assert "positive_change_not_over_analyzed" in reception["allowed_surface_intents"]
    assert plan["case_id_branch_used"] is False
    assert plan["public_response_key_added"] is False
    assert plan["comment_text_generated"] is False


def test_phase5_low_information_ratio_keeps_light_observation_and_prompt_policy() -> None:
    meta = build_emlis_ai_state_answer_ratio_policy(
        {
            "id": "phase5-low-information",
            "created_at": "2026-06-01T00:00:00Z",
            "memo": "無理",
            "memo_action": "",
            "emotions": ["疲れ"],
            "emotion_details": [{"type": "疲れ", "strength": "medium"}],
            "category": ["生活"],
            "is_secret": False,
        }
    ).as_meta()

    ratio = meta["resolved_ratio"]
    reception_summary = meta["resolver_context"]["reception_mode_summary"]
    assert reception_summary["reception_mode_id"] == "low_information_question"
    assert reception_summary["low_information_question_required"] is True
    assert ratio["reason"] == "low_information_light_prompt"
    assert ratio["range_key"] == "low_information"
    assert ratio["observation"] == 0.25
    assert ratio["human_follow"] == 0.75
    unit_plan = meta["ratio_basis"]["section_role_unit_plan"]
    assert unit_plan["observation_units"] == 1
    assert unit_plan["human_follow_units"] == 1
    assert unit_plan["total_units"] == 2
    assert meta["comment_text_generated"] is False
    assert meta["public_response_key_added"] is False
    assert meta["raw_input_included"] is False
