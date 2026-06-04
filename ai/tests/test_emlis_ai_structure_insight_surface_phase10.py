# -*- coding: utf-8 -*-
from __future__ import annotations

from emlis_ai_complete_composer_types import CompleteSentencePlanLine, CompleteSentencePlanV2
from emlis_ai_complete_surface_realizer import build_complete_surface_realization_v2
from emlis_ai_structure_insight_surface import (
    build_structure_insight_surface_for_line,
)
from emlis_ai_two_stage_section_surface_plan import build_two_stage_section_surface_plan


def _two_stage_line(
    *,
    sentence_id: str,
    roles: tuple[str, ...],
    section_id: str,
    order_index: int,
    mode_id: str,
    coverage_group: str = "structure_question",
    line_role: str = "opening",
    relation_type: str = "approach_avoidance",
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
            "coverage_group": coverage_group,
            "two_stage_section_id": section_id,
            "two_stage_section_role": "state_answer_observation" if section_id == "observation" else "human_reception",
            "two_stage_display_label": label,
            "two_stage_comment_text_section_label": f"{label}：",
            "two_stage_section_label_required": True,
            "two_stage_section_order_index": order_index,
            "two_stage_expected_comment_text_shape": "labelled_two_stage_text",
            "two_stage_section_surface_plan_required": True,
            "two_stage_reception_mode_id": mode_id,
            "two_stage_ratio_reason": "structure_question_observation_thickened",
            "allowed_surface_intents": (
                "structure_insight_surface_limited_family",
                "observation_insight_seed" if section_id == "observation" else "structure_insight_temperature_support",
                "soft_inference_surface_required",
            ),
        },
    )


def _plan(mode_id: str, coverage_group: str = "structure_question") -> CompleteSentencePlanV2:
    return CompleteSentencePlanV2(
        plan_id=f"phase10_{mode_id}_{coverage_group}",
        coverage_group=coverage_group,
        sentence_budget=2,
        sentence_plans=(
            _two_stage_line(
                sentence_id="phase10_observation",
                roles=("wish_slot", "blockage_slot", "fatigue_reaction_slot"),
                section_id="observation",
                order_index=0,
                mode_id=mode_id,
                coverage_group=coverage_group,
                relation_type="approach_avoidance",
            ),
            _two_stage_line(
                sentence_id="phase10_reception",
                roles=("temperature_support", "soft_boundary"),
                section_id="reception",
                order_index=1,
                mode_id=mode_id,
                coverage_group=coverage_group,
                line_role="relation",
                relation_type="approach_avoidance",
            ),
        ),
        meta={
            "two_stage_section_surface_plan_required": True,
            "two_stage_expected_comment_text_shape": "labelled_two_stage_text",
            "two_stage_section_labels_required": True,
        },
    )


def test_phase10_connects_one_soft_insight_seed_for_structure_question() -> None:
    realization = build_complete_surface_realization_v2(sentence_plan=_plan("structure_question_observation"))

    assert realization.status == "ready"
    assert realization.comment_text.startswith("見えたこと：\n")
    assert "\n\nEmlisから：\n" in realization.comment_text
    observation, reception = realization.comment_text.split("\n\nEmlisから：\n", 1)
    observation = observation.removeprefix("見えたこと：\n")
    assert "ように見えます" in observation
    assert "受け取れます" in reception
    assert "原因は" not in realization.comment_text
    assert "性格" not in realization.comment_text
    assert "診断" not in realization.comment_text

    summary = realization.two_stage_surface_realization["structure_insight_surface"]
    assert summary["applied"] is True
    assert summary["phase10_structure_insight_surface_connected"] is True
    assert summary["observation_insight_seed_count"] == 1
    assert summary["reception_temperature_support_count"] == 1
    assert summary["insight_delta_blind_qa_floor_candidate"] == "YELLOW"
    assert summary["overclaim_count"] == 0
    assert summary["diagnosis_count"] == 0
    assert summary["personality_claim_count"] == 0
    assert summary["mirror_only_reduction_supported"] is True
    assert summary["comment_text_body_included"] is False
    assert summary["raw_input_included"] is False
    assert summary["public_response_key_added"] is False

    meta = realization.as_meta(include_realized_text=False)
    assert meta["structure_insight_surface_applied"] is True
    assert meta["phase10_structure_insight_surface_connected"] is True
    assert meta["structure_insight_surface_insight_delta_blind_qa_floor_candidate"] == "YELLOW"
    assert meta["structure_insight_surface_public_response_key_added"] is False
    assert meta["public_response_key_change"] is False
    assert meta["rn_visible_title_changed"] is False
    assert meta["raw_input_included"] is False
    assert meta["comment_text_body_included"] is False


def test_phase10_supports_long_meaning_arc_without_requiring_mode_branch() -> None:
    realization = build_complete_surface_realization_v2(sentence_plan=_plan("standard_state_answer", coverage_group="long_meaning_arc"))

    assert realization.status == "ready"
    assert "いくつかの核" in realization.comment_text
    summary = realization.two_stage_surface_realization["structure_insight_surface"]
    assert "long_meaning_arc" in summary["limited_families"]
    assert summary["observation_insight_seed_count"] == 1
    assert summary["insight_delta_blind_qa_floor_candidate"] == "YELLOW"


def test_phase10_does_not_force_deep_insight_for_daily_unpleasant_or_low_information() -> None:
    for mode_id, coverage_group in (
        ("daily_unpleasant_reception", "daily_unpleasant"),
        ("low_information_question", "low_information_short"),
    ):
        realization = build_complete_surface_realization_v2(sentence_plan=_plan(mode_id, coverage_group=coverage_group))
        summary = realization.two_stage_surface_realization
        assert summary.get("structure_insight_surface_applied") is False
        assert summary.get("phase10_structure_insight_surface_connected") is False
        assert "structure_insight_surface" not in summary or summary["structure_insight_surface"] == {}


def test_phase10_gate_blocks_hard_overclaim_before_surface() -> None:
    line = _two_stage_line(
        sentence_id="phase10_unsafe_overclaim",
        roles=("wish_slot", "blockage_slot", "fatigue_reaction_slot"),
        section_id="observation",
        order_index=0,
        mode_id="structure_question_observation",
    )
    text, meta = build_structure_insight_surface_for_line(
        line,
        section_id="observation",
        two_stage_meta=line.meta,
        proposed_surface_override="原因は本人の性格です。",
    )

    assert text == ""
    assert meta["structure_insight_surface_gate_passed"] is False
    assert meta["structure_insight_surface_applied"] is False
    assert meta["structure_insight_surface_gate_rejection_reasons"]
    assert meta["structure_insight_surface_public_response_key_added"] is False
    assert meta["structure_insight_surface_comment_text_body_included"] is False


def test_phase10_section_plan_marks_limited_connection_without_public_change() -> None:
    plan = build_two_stage_section_surface_plan(
        {
            "two_stage_display_required": True,
            "section_labels_required": True,
            "expected_comment_text_shape": "labelled_two_stage_text",
            "reception_mode_id": "structure_question_observation",
            "resolved_ratio": {"reason": "structure_question_observation_thickened"},
            "sections": [
                {
                    "section_id": "observation",
                    "section_role": "state_answer_observation",
                    "sentence_plan_unit_count": 1,
                },
                {
                    "section_id": "reception",
                    "section_role": "human_follow",
                    "reception_section_role": "emlis_reception",
                    "sentence_plan_unit_count": 2,
                },
            ],
        },
        composition_contract={"two_stage_reception_surface_required": True},
    )
    sections = {section["section_id"]: section for section in plan["sections"]}
    assert "observation_insight_seed" in sections["observation"]["allowed_surface_intents"]
    assert "structure_insight_temperature_support" in sections["reception"]["allowed_surface_intents"]
    assert plan["section_budget_policy"]["phase10_structure_insight_surface_connection_supported"] is True
    assert plan["public_response_key_added"] is False
    assert plan["rn_visible_contract_changed"] is False
